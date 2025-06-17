import pexpect
import logging
import shutil
import os
import argparse
from verify_checksum_json import validate_directory

GLOBAL_TIMEOUT = 300

logging.basicConfig(filename='test_startup.log', filemode='w', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_files(folder = "$HOME/.local/share/MoondreamStation"):
    folder = os.path.expanduser(folder)
    if os.path.exists(folder):
        logging.debug(f"Attempting to clean folder...{folder}")
        shutil.rmtree(folder)
    if not os.path.exists(folder):
        logging.debug(f"Successfully cleaned {folder}")
        return
    else:
        logging.debug(f"Folder was not cleaned.")

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
    
    # force close for now
    if child.isalive():
        child.close(force=True)
    
def check_health(child):
    child.sendline('health')
    child.expect('moondream>', timeout=30)
    health_prompt = child.before.decode()
    logging.debug("Health Check.")
    logging.debug(health_prompt)
    return child

def validate_files(dir_path, expected_json):
    result = validate_directory(dir_path, expected_json)
    
    if result.get('error'):
        logging.debug(f"Validation error: {result['error']}")
        return result
    
    if result['valid']:
        logging.debug(f"File validation PASSED: {result['found']}/{result['total_expected']} files valid")
    else:
        missing_count = len(result.get('missing', []))
        mismatched_count = len(result.get('mismatched', []))
        
        if missing_count > 0 and mismatched_count > 0:
            logging.debug(f"File validation FAILED: {result['found']}/{result['total_expected']} files found, {missing_count} missing, {mismatched_count} mismatched")
        elif missing_count > 0:
            logging.debug(f"File validation FAILED: {result['found']}/{result['total_expected']} files found, {missing_count} missing")
        elif mismatched_count > 0:
            logging.debug(f"File validation FAILED: {result['found']}/{result['total_expected']} files found, {mismatched_count} hash mismatched")
        
        if result.get('missing'):
            logging.debug(f"Missing files: {result['missing']}")
        if result.get('mismatched'):
            logging.debug(f"Mismatched files: {result['mismatched']}")
    
    return result

def test_startup(child, backend_path="~/.local/share/MoondreamStation", checksum_path="expected_checksum.json"):
    validate_files(os.path.expanduser(backend_path), checksum_path)
    return child

def test_server(cleanup=True, executable_path='./moondream_station', server_args=None):
    if cleanup:
        clean_files()

    child = start_server(executable_path, server_args)
    child = check_health(child)
    child = test_startup(child)
    
    end_server(child)

def main():
    parser = argparse.ArgumentParser(description='Test Moondream Station startup')
    parser.add_argument('--no-cleanup', action='store_true', help='Skip cleanup before test')
    parser.add_argument('--executable', default='./moondream_station', help='Path to moondream_station executable')
    
    args, server_args = parser.parse_known_args()
    
    test_server(cleanup=not args.no_cleanup, executable_path=args.executable, server_args=server_args)

if __name__ == "__main__":
    main()