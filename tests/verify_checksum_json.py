import os
import json
import hashlib
import sys

def get_md5(filepath):
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except (IOError, OSError):
        return None

def scan_directory(root_path):
    result = {}
    for root, dirs, files in os.walk(root_path):
        for file in files:
            full_path = os.path.join(root, file)
            if os.path.isfile(full_path):
                rel_path = os.path.relpath(full_path, root_path).replace('\\', '/')
                md5_hash = get_md5(full_path)
                if md5_hash:
                    result[rel_path] = md5_hash
    return result

def validate_directory(dir_path, expected_json_path):
    with open(expected_json_path, 'r') as f:
        expected = json.load(f)
    
    missing = []
    mismatched = []
    
    for rel_path, expected_hash in expected.items():
        full_path = os.path.join(dir_path, rel_path)
        if not os.path.isfile(full_path):
            missing.append(rel_path)
        elif get_md5(full_path) != expected_hash:
            mismatched.append(rel_path)
    
    return {'missing': missing, 'mismatched': mismatched, 'valid': not (missing or mismatched)}

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python validator.py <directory_path> <expected_json_path>")
        sys.exit(1)
    
    result = validate_directory(sys.argv[1], sys.argv[2])
    
    if result['valid']:
        print("All expected files present with correct checksums")
    else:
        if result['missing']:
            print(f"Missing files: {result['missing']}")
        if result['mismatched']:
            print(f"Checksum mismatch: {result['mismatched']}")