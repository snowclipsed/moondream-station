import socket
import logging
import os
import shutil
import psutil
from verify_checksum_json import validate_directory

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

def is_port_occupied(port, host='localhost'):
   with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
       return s.connect_ex((host, port)) == 0
   
def get_port_process_pid(port):
    for proc in psutil.process_iter(['pid', 'connections']):
        try:
            connections = proc.info['connections'] or []
            for conn in connections:
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def get_process_start_time(pid):
    try:
        proc = psutil.Process(pid)
        return proc.create_time()
    except:
        return None