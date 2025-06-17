import os
import re
import json
import socket
import logging
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

def load_expected_responses(json_path="expected_responses.json"):
    """Load expected responses from JSON file"""
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load expected responses: {e}")
        return {}

def clean_response_output(output, command_type):
    if command_type == 'caption':
        lines = output.split('\n')
        caption_started = False
        caption_lines = []
        
        for line in lines:
            line = line.strip()
            if 'Generating streaming caption...' in line:
                caption_started = True
                continue
            elif caption_started and line and not line.startswith('caption '):
                caption_lines.append(line)
        
        if caption_lines:
            return ' '.join(caption_lines)
        
        return output.strip()
    
    elif command_type == 'detect':
        if 'No' in output and 'detected' in output:
            return "No face objects detected"
        else:
            match = re.search(r"Position: (\{[^}]+\})", output)
            if match:
                return match.group(1)
            return output.strip()
    
    elif command_type == 'point':
        match = re.search(r"(\{'x': [^}]+\})", output)
        if match:
            return match.group(1)
        return output.strip()
    
    else:
        return output.strip()

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