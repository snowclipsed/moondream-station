import pexpect
import logging
import shutil
import os
import argparse
from utils import is_port_occupied, validate_files, clean_files

GLOBAL_TIMEOUT = 300

def setup_logging(verbose=False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = logging.FileHandler('test_startup.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler (only if verbose)
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

def test_startup(child, hypervisor_occupied, inference_occupied, backend_path="~/.local/share/MoondreamStation", checksum_path="expected_checksum.json"):
    logging.debug(f"Hypervisor Port was {'occupied' if hypervisor_occupied else 'not occupied'} before the model startup.")
    logging.debug(f"Inference Server Port was {'occupied' if inference_occupied else 'not occupied'} before the model startup.")

    validate_files(os.path.expanduser(backend_path), checksum_path)
    
    hypervisor_occupied = is_port_occupied(2020)
    inference_occupied = is_port_occupied(20200)
    
    logging.debug(f"Hypervisor Port is currently {'occupied' if hypervisor_occupied else 'not occupied'}")
    logging.debug(f"Inference Server Port is currently {'occupied' if inference_occupied else 'not occupied'}")
    
    return child

def test_server(cleanup=True, executable_path='./moondream_station', server_args=None):
    if cleanup:
        clean_files()

    hypervisor_occupied = is_port_occupied(2020)
    inference_occupied = is_port_occupied(20200)

    child = start_server(executable_path, server_args)
    child = check_health(child)
    child = test_startup(child, hypervisor_occupied, inference_occupied)
    
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