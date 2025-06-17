import os
import json
import hashlib

DEFAULT_IGNORE_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', '.pytest_cache', 'py_versions'}
DEFAULT_IGNORE_FILES = {'__init__.py', '.DS_Store', 'Thumbs.db', '.gitignore'}

def get_md5(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def should_ignore(name, ignore_set):
    return name in ignore_set or any(name.endswith(pattern.lstrip('*')) for pattern in ignore_set if '*' in pattern)

def generate_json(root_path, ignore_dirs=None, ignore_files=None, output_file=None):
    ignore_dirs = ignore_dirs or DEFAULT_IGNORE_DIRS
    ignore_files = ignore_files or DEFAULT_IGNORE_FILES
    
    result = {}
    
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if not should_ignore(d, ignore_dirs)]
        
        rel_root = os.path.relpath(root, root_path)
        if rel_root == '.':
            rel_root = ''
        
        for file in files:
            if should_ignore(file, ignore_files):
                continue
                
            rel_path = os.path.join(rel_root, file) if rel_root else file
            full_path = os.path.join(root, file)
            
            try:
                result[rel_path.replace('\\', '/')] = get_md5(full_path)
            except (IOError, OSError):
                continue
    
    json_output = json.dumps(result, indent=2, sort_keys=True)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(json_output)
        print(f"Generated {output_file}")
    else:
        print(json_output)
    
    return result

if __name__ == '__main__':
    import sys
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('-o', '--output', help='Output JSON file')
    parser.add_argument('--ignore-dirs', nargs='*', help='Additional directories to ignore')
    parser.add_argument('--ignore-files', nargs='*', help='Additional files to ignore')
    
    args = parser.parse_args()
    
    ignore_dirs = DEFAULT_IGNORE_DIRS.copy()
    ignore_files = DEFAULT_IGNORE_FILES.copy()
    
    if args.ignore_dirs:
        ignore_dirs.update(args.ignore_dirs)
    if args.ignore_files:
        ignore_files.update(args.ignore_files)
    
    generate_json(args.directory, ignore_dirs, ignore_files, args.output)