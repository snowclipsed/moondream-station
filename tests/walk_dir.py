import hashlib
import json
from pathlib import Path

def verify_structure(manifest_file, base_path='.'):
    """Verify directory structure and file hashes against manifest"""
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)
    
    base_path = Path(base_path)
    
    # Check directories
    for dir_path in manifest['directories']:
        if not (base_path / dir_path).is_dir():
            print(f"Missing directory: {dir_path}")
            return False
    
    # Check files and hashes
    for file_path, expected_hash in manifest['files'].items():
        full_path = base_path / file_path
        
        if not full_path.is_file():
            print(f"Missing file: {file_path}")
            return False
            
        if expected_hash is not None:
            hash_md5 = hashlib.md5()
            with open(full_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            
            if hash_md5.hexdigest() != expected_hash:
                print(f"Hash mismatch: {file_path}")
                return False
    
    return True