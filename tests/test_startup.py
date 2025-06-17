import pexpect
import logging
import shutil
import os
import argparse
from utils import is_port_occupied, validate_files, clean_files, load_expected_responses, clean_response_output

GLOBAL_TIMEOUT = 300

def setup_logging(verbose=False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    file_handler = logging.FileHandler('test_startup.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    if verbose:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

def start_server(executable_path='./moondream_station', args=None):
    cmd = [executable_path]
    if args:
        cmd.extend(args)
    child = pexpect.spawn(' '.join(cmd))
    logging.debug(f"Starting up Moondream Station with command: {' '.join(cmd)}")
    child.expect('moondream>', timeout=30)
    return child

def end_server(child):
    # just check for exit message, don't wait for process to die, since bad shutdown in a known bug.
    child.sendline('exit')
    child.expect(r'Exiting Moondream CLI', timeout=10)
    
    # force close for now?
    # TODO: see if we can refactor this
    if child.isalive():
        child.close(force=True)
    
def check_health(child):
    child.sendline('health')
    child.expect('moondream>', timeout=30)
    health_prompt = child.before.decode()
    logging.debug("Health Check.")
    logging.debug(health_prompt)
    return child

def parse_model_list_output(output):
    models = []
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('Model: '):
            models.append(line[7:].strip())
    return models

def test_startup(child, hypervisor_occupied, inference_occupied, backend_path="~/.local/share/MoondreamStation", checksum_path="expected_checksum.json"):
    logging.debug(f"Hypervisor Port was {'occupied' if hypervisor_occupied else 'not occupied'} before the model startup.")
    logging.debug(f"Inference Server Port was {'occupied' if inference_occupied else 'not occupied'} before the model startup.")

    validate_files(os.path.expanduser(backend_path), checksum_path)
    
    hypervisor_occupied = is_port_occupied(2020)
    inference_occupied = is_port_occupied(20200)
    
    logging.debug(f"Hypervisor Port is currently {'occupied' if hypervisor_occupied else 'not occupied'}")
    logging.debug(f"Inference Server Port is currently {'occupied' if inference_occupied else 'not occupied'}")
    # TODO: Add more reliable hypervisor checking.

    return child

def test_capability(child, command, expected_response, timeout=60):
    logging.debug(f"Testing: {command}")
    
    child.sendline(command)
    
    if 'caption' in command:
        try:
            child.expect('Generating streaming caption...', timeout=10)
            child.expect('moondream>', timeout=timeout)
        except:
            child.expect('moondream>', timeout=timeout)
    else:
        child.expect('moondream>', timeout=timeout)
    
    output = child.before.decode().strip()
    
    command_type = None
    if 'caption' in command:
        command_type = 'caption'
    elif 'query' in command:
        command_type = 'query'
    elif 'detect' in command:
        command_type = 'detect'
    elif 'point' in command:
        command_type = 'point'
    
    cleaned_output = clean_response_output(output, command_type)
    
    # Use keyword matching for caption and query, exact matching for detect and point
    if command_type in ['caption', 'query']:
        keywords = expected_response.get('keywords', [])
        matches = sum(1 for keyword in keywords if keyword.lower() in cleaned_output.lower())
        success = matches >= len(keywords) * 0.7  # 70% keyword match
        logging.debug(f"Keywords matched: {matches}/{len(keywords)} ({'PASS' if success else 'FAIL'})")
    else:
        success = cleaned_output == expected_response
        logging.debug(f"Exact match: {'PASS' if success else 'FAIL'}")
    
    logging.debug(f"Expected: {expected_response}")
    logging.debug(f"Got: {cleaned_output}")
    
    return success, cleaned_output

def test_model_capabilities(child, model_name):
    image_url = "https://raw.githubusercontent.com/m87-labs/moondream-station/refs/heads/main/assets/md_logo_clean.png"
    
    expected_responses = load_expected_responses()
    if model_name not in expected_responses:
        logging.error(f"No expected responses found for model: {model_name}")
        return child
    
    model_expected = expected_responses[model_name]
    
    capabilities = [
        {
            'command': f'caption {image_url}',
            'expected': model_expected['caption'],
            'name': 'Caption'
        },
        {
            'command': f'query "What is in this image?" {image_url}',
            'expected': model_expected['query'],
            'name': 'Query'
        },
        {
            'command': f'detect face {image_url}',
            'expected': model_expected['detect'],
            'name': 'Detect'
        },
        {
            'command': f'point face {image_url}',
            'expected': model_expected['point'],
            'name': 'Point'
        }
    ]
    
    results = {}
    for cap in capabilities:
        try:
            success, output = test_capability(child, cap['command'], cap['expected'])
            results[cap['name']] = {'success': success, 'output': output}
        except Exception as e:
            logging.error(f"{cap['name']} test failed: {e}")
            results[cap['name']] = {'success': False, 'output': str(e)}
    
    passed = sum(1 for r in results.values() if r['success'])
    total = len(results)
    logging.debug(f"Model capability tests: {passed}/{total} passed for {model_name}")
    
    return child

def test_all_models(child):
    child.sendline('admin model-list')
    child.expect('moondream>', timeout=30)
    model_list_output = child.before.decode()
    logging.debug("Model list output:")
    logging.debug(model_list_output)
    
    models = parse_model_list_output(model_list_output)
    logging.debug(f"Found {len(models)} models: {models}")
    logging.debug("")
    
    for model_name in models:
        logging.debug(f"Testing model: {model_name}")
        
        child.sendline(f'admin model-use "{model_name}" --confirm')
        try:
            child.expect('Model initialization completed successfully!', timeout=120)
            child.expect('moondream>', timeout=10)
            logging.debug(f"Successfully switched to model: {model_name}")
            logging.debug("")
            
            child = test_model_capabilities(child, model_name)
            
        except Exception as e:
            logging.warning(f"Model switch to '{model_name}' failed: {e}")
    
    return child

def test_server(cleanup=True, executable_path='./moondream_station', server_args=None):
    if cleanup:
        clean_files()

    pre_hypervisor = is_port_occupied(2020)
    pre_inference = is_port_occupied(20200)

    child = start_server(executable_path, server_args)
    child = check_health(child)
    child = test_startup(child, pre_hypervisor, pre_inference)
    child = test_all_models(child)
    
    end_server(child)

def main():
    parser = argparse.ArgumentParser(description='Test Moondream Station startup')
    parser.add_argument('--no-cleanup', action='store_true', help='Skip cleanup before test')
    parser.add_argument('--executable', default='./moondream_station', help='Path to moondream_station executable')
    parser.add_argument('--verbose', action='store_true', help='Print log messages to console')
    
    args, server_args = parser.parse_known_args()
    
    setup_logging(verbose=args.verbose)
    
    test_server(cleanup=not args.no_cleanup, executable_path=args.executable, server_args=server_args)

if __name__ == "__main__":
    main()