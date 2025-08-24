import os
import json
from unicodedata import normalize
import string

def write_token_to_file(token: str, user_id: str = None):
    try:
        file_path = os.getenv("VEXGEN_TOKEN_FILE")
        
        # Expand user home directory (~)
        file_path = os.path.expanduser(file_path)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Create JSON data
        token_data = {
            "user_id": user_id,
            "token": token
        }
        
        # Create/write to file (automatically creates if doesn't exist)
        with open(file_path, 'w') as file:
            json.dump(token_data, file, indent=2)
        os.chmod(file_path, 0o600)

    except Exception as e:
        print(f"Failed to write token to file: {e}")
        
        

def os_path_separators():
    seps = []
    for sep in os.path.sep, os.path.altsep:
        if sep:
            seps.append(sep)
    return seps

def sanitise_filesystem_name(potential_file_path_name):
    # Sort out unicode characters
    valid_filename = normalize('NFKD', potential_file_path_name).encode('ascii', 'ignore').decode('ascii')
    # Replace path separators with underscores
    for sep in os_path_separators():
        valid_filename = valid_filename.replace(sep, '_')
    # Ensure only valid characters
    valid_chars = "-_.() {0}{1}".format(string.ascii_letters, string.digits)
    valid_filename = "".join(ch for ch in valid_filename if ch in valid_chars)
    # Ensure at least one letter or number to ignore names such as '..'
    valid_chars = "{0}{1}".format(string.ascii_letters, string.digits)
    test_filename = "".join(ch for ch in potential_file_path_name if ch in valid_chars)
    if len(test_filename) == 0:
        # Replace empty file name or file path part with the following
        valid_filename = "(Empty Name)"
    return valid_filename

def path_split_into_list(path):
    # Gets all parts of the path as a list, excluding path separators
    parts = []
    while True:
        newpath, tail = os.path.split(path)
        if newpath == path:
            assert not tail
            if path and path not in os_path_separators():
                parts.append(path)
            break
        if tail and tail not in os_path_separators():
            parts.append(tail)
        path = newpath
    parts.reverse()
    return parts

def sanitise_filesystem_path(potential_file_path):
    # Splits up a path and sanitises the name of each part separately
    path_parts_list = path_split_into_list(potential_file_path)
    sanitised_path = ''
    for path_component in path_parts_list:
        sanitised_path = '{0}{1}{2}'.format(sanitised_path, sanitise_filesystem_name(path_component), os.path.sep)
    return sanitised_path

def check_if_path_is_under(parent_path, child_path):
    # Using the function to split paths into lists of component parts, check that one path is underneath another
    child_parts = path_split_into_list(child_path)
    parent_parts = path_split_into_list(parent_path)
    if len(parent_parts) > len(child_parts):
        return False
    return all(part1==part2 for part1, part2 in zip(child_parts, parent_parts))

def make_valid_file_path(path, root_path):
    if path:
        sanitised_path = sanitise_filesystem_path(path)
        complete_path = os.path.join(root_path, sanitised_path)
    else:
        complete_path = complete_path
    complete_path = os.path.abspath(complete_path)
    if check_if_path_is_under(root_path, complete_path):
        return complete_path
    else:
        return None