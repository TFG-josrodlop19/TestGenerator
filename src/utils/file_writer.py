import os

def write_token_to_file(token: str):
    try:
        file_path = os.getenv("VEXGEN_TOKEN_FILE")
        
        # Expand user home directory (~)
        file_path = os.path.expanduser(file_path)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Create/write to file (automatically creates if doesn't exist)
        print(file_path)
        with open(file_path, 'w') as file:
            file.write(token)
        os.chmod(file_path, 0o600)

    except Exception as e:
        print(f"Failed to write token to file: {e}")