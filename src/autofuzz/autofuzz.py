import os
import shutil
import subprocess
import sys
from pathlib import Path
from utils.file_writer import generate_path_repo
from utils.classes import TestStatus
from database.operations import get_created_fuzzers_by_project, update_fuzzer_status
from database.models import Fuzzer, ConfidenceLevel
import re

def handle_readonly(func, path, exc):
    os.chmod(path, 0o755)
    func(path)

def build_tests(owner: str, name: str):
    """
    Executes the OSS-Fuzz build_fuzzers command to compile the generated fuzz tests.
    """
    fuzzers = get_created_fuzzers_by_project(owner, name)
    
    if fuzzers is None or fuzzers == []:
        raise ValueError(f"No test info generated for {owner}/{name}")
    repo_path = generate_path_repo(owner, name)
    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
    
    project = Path(repo_path).name
    
    
    # Change to the OSS-Fuzz root directory
    oss_fuzz_root = Path(repo_path).parent.parent
    if not oss_fuzz_root.exists():
        raise FileNotFoundError(f"OSS-Fuzz root does not exist: {oss_fuzz_root}")
    
    # Clean previous build outputs
    build_out_dir = oss_fuzz_root / "build" / "out" / project
    if build_out_dir.exists():
        print(f"Cleaning previous build directory: {build_out_dir}")
        try:
            shutil.rmtree(build_out_dir, onerror=handle_readonly)
        except Exception:
            print(f"Error cleaning build directory: {build_out_dir}")
    try:
        # Execute the build_fuzzers command using the venv Python
        print(f"Building fuzzers for project: {project}")
        
        print(f"Command: {sys.executable} infra/helper.py build_fuzzers {project}")
        
        result = subprocess.run([
            sys.executable,  # Use the current Python interpreter
            "infra/helper.py", 
            "build_fuzzers", 
            project
        ],
        cwd=oss_fuzz_root,  # Change working directory
        capture_output=True, 
        text=True, 
        check=True
        )
        
        print("Build successful!")
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        check_compilation_failures(owner, name, fuzzers)
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed with return code: {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error during build: {e}")
        return False

def check_compilation_failures(owner: str, name: str, fuzzers: list[Fuzzer]):
    repo_path = generate_path_repo(owner, name)
    project = Path(repo_path).name
    
    # OSS-Fuzz build output directory
    oss_fuzz_root = Path(repo_path).parent.parent
    build_out_dir = oss_fuzz_root / "build" / "out" / project    
    for fuzzer in fuzzers:
        if fuzzer and not fuzzer.testPath == "" and not fuzzer.name == "":
            compiled_fuzzer_name = fuzzer.name + ".class"
            files = list(build_out_dir.rglob(compiled_fuzzer_name))
            if not files:
                update_fuzzer_status(fuzzer.id, TestStatus.ERROR_BUILDING)


def execute_tests(owner: str, name: str, confidence: ConfidenceLevel):
    repo_path = generate_path_repo(owner, name)
    project = Path(repo_path).name
    confidence = confidence.get_timeout_seconds()
    
    # Directorio donde OSS-Fuzz guarda los binarios compilados
    oss_fuzz_root = Path(repo_path).parent.parent
    
    # Obtener información de tests generados
    try:
        fuzzers = get_created_fuzzers_by_project(owner, name)
    except FileNotFoundError:
        print(f"No test info found for {owner}/{name}")
        return {}

    for fuzzer in fuzzers:
        if fuzzer and not (fuzzer.testPath == "" or fuzzer.name == ""):
            fuzzer_name = fuzzer.name
            print(f"Executing fuzzer: {fuzzer_name}")
            try:
                # Exec each fuzzer individually
                if fuzzer.usesParameters:
                    result = subprocess.run([
                        sys.executable,
                        "infra/helper.py", 
                        "run_fuzzer", 
                        project,
                        fuzzer_name,
                        "--",
                        f"-max_total_time={confidence}",
                        "-print_final_stats=1"
                    ], 
                    cwd=oss_fuzz_root,
                    capture_output=True, 
                    text=True
                    )
                else:
                    result = subprocess.run([
                        sys.executable,
                        "infra/helper.py", 
                        "run_fuzzer", 
                        project,
                        fuzzer_name,
                        "--",
                        "-runs=1",
                        "-print_final_stats=1"
                    ], 
                    cwd=oss_fuzz_root,
                    capture_output=True, 
                    text=True
                    )
                
                # Analyze results
                output = result.stdout + result.stderr
                
                if result.returncode == 0:
                    # No vulnerabilities found
                    print(f"✅ {fuzzer_name}: Completed without finding vulnerabilities.")
                    update_fuzzer_status(fuzzer.id, TestStatus.NOT_VULNERABLE)
                else:
                    # Fuzzer found a vulnerability or crashed
                    if any(keyword in output for keyword in ["ASAN", "heap-buffer-overflow", "AddressSanitizer", "SEGV", "abrt", "FuzzerSecurityIssue", "DEDUP_TOKEN"]):
                        print(f"❌ {fuzzer_name}: Vulnerability found!")
                        crash_info = extract_vulnerability_info(output)
                        update_fuzzer_status(fuzzer.id, TestStatus.VULNERABLE, crash_info=crash_info)
                    else:
                        print(f"⚠️ {fuzzer_name}: Execution error")
                        update_fuzzer_status(fuzzer.id, TestStatus.ERROR_EXECUTING)
            except Exception as e:
                print(f"💥 {fuzzer_name}: Unexpected error: {e}")
                update_fuzzer_status(fuzzer.id, TestStatus.ERROR_EXECUTING)

def extract_vulnerability_info(output: str) -> dict:
    """
    Extracts vulnerability type and description from the fuzzer output.
    """
    # Pattern to capture the type and description of the vulnerability
    pattern = r"FuzzerSecurityIssue(?:High|Medium|Low)?: ([^\n]+)\n(.*?)(?=\n\tat|$)"
    
    match = re.search(pattern, output, re.DOTALL)
    if match:
        vulnerability_type = match.group(1).strip()
        description = match.group(2).strip()
        
        return {
            'type': vulnerability_type.replace("\n", " "),
            'description': description.replace("\n", " ")
        }
    
    return None