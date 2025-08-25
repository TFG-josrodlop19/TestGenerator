import subprocess


def clone_repo(owner: str, name: str, dest_path: str):
    """
    Clones a GitHub repository to the specified destination path.
    First tries SSH, then falls back to HTTPS if SSH fails.
    """
    ssh_url = f"git@github.com:{owner}/{name}.git"
    https_url = f"https://github.com/{owner}/{name}.git"
    
    # Try SSH first
    try:
        print(f"Attempting to clone with SSH: {ssh_url}")
        result = subprocess.run(
            ["git", "clone", ssh_url, dest_path], 
            capture_output=True, 
            text=True, 
            check=True
        )
        print(f"Successfully cloned repository with SSH to: {dest_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"SSH clone failed: {e.stderr}")
        print(f"Falling back to HTTPS: {https_url}")
        
        # Try HTTPS as fallback
        try:
            result = subprocess.run(
                ["git", "clone", https_url, dest_path], 
                capture_output=True, 
                text=True, 
                check=True
            )
            print(f"Successfully cloned repository with HTTPS to: {dest_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"HTTPS clone also failed: {e.stderr}")
            print(f"Failed to clone repository {owner}/{name}")
            return False