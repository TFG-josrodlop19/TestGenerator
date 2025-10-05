import os
import stat
import shutil
import subprocess
import sys
from pathlib import Path
from java_analyzer.spoon_reader import get_artifact_info
from utils.file_writer import generate_path_repo, resolve_path
from utils.git_utils import clone_repo
from database.operations import create_project, get_created_fuzzers_by_project, create_vulnerabilities_artifacts, update_fuzzer_status, get_last_scanner_all_data_by_project, get_last_scanner_data_by_project, get_scanner_by_id, get_scanner_all_data_by_id
from database.models import Fuzzer, ConfidenceLevel, VulnerabilityStatus, TestStatus
from vexgen_caller.vex_generator import generate_vex, get_tix_data
from test_generator.generator import generate_fuzzers, generate_fuzzer_for_failed_artifacts
import re
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.text import Text


def generate_fuzz_tests(owner: str, name: str, pom_path: str, confidence: ConfidenceLevel=ConfidenceLevel.MEDIUM, reload: bool = True):
    # Path for cloning the repository inside OSS-Fuzz/projects
    dest_path = Path(generate_path_repo(owner, name))
    clone_repo(owner, name, dest_path)
    
    print(f"Cloned repository to: {dest_path}")

    resolved_pom_path = resolve_path(pom_path, dest_path)

        
    # Verify that the pom.xml file exists
    if not resolved_pom_path.exists():
        raise FileNotFoundError(f"Error: POM file not found at {resolved_pom_path}")

    # Initialize the project in the database with a new scanner
    project = create_project(owner, name, pom_path, confidence)
    
    vulnerabilities = None
    if not reload:
        try:
            vulnerabilities, artifacts_json = get_tix_data(owner, name)
            print(f"Using existing TIX file")
        except FileNotFoundError:
            print(f"TIX file not found, generating a new one...")
            generate_vex(owner, name)
            vulnerabilities, artifacts_json = get_tix_data(owner, name)
    else:
        generate_vex(owner, name)
        vulnerabilities, artifacts_json = get_tix_data(owner, name)

    if not vulnerabilities or len(vulnerabilities) == 0:
        print("No vulnerabilities found in the TIX file.")
        return

    create_vulnerabilities_artifacts(project.id, vulnerabilities)
    
    # Generate artifacts info with Spoon
    artifacts_data = None
    if artifacts_json and artifacts_json != "[]":
        artifacts_data = get_artifact_info(str(resolved_pom_path), artifacts_json)
    else:
        print("No artifacts found in the VEX file.")
        return
    
    if artifacts_data:
        generate_fuzzers(owner, name, artifacts_data)
        generate_fuzzer_for_failed_artifacts(owner, name)
        print("Test generation completed.")
        print(f"Test saved in: {dest_path}")
        return True
    else:
        print("No artifacts data extracted.")
        return False

def build_tests(owner: str, name: str):
    """
    Executes the OSS-Fuzz build_fuzzers command to compile the generated fuzz tests.
    """
    fuzzers = get_created_fuzzers_by_project(owner, name)
    
    if fuzzers is None or fuzzers == []:
        raise FileNotFoundError(f"No tests generated for {owner}/{name}")
    repo_path = generate_path_repo(owner, name)
    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
    
    project = Path(repo_path).name
    
    
    # Change to the OSS-Fuzz root directory
    oss_fuzz_root = Path(repo_path).parent.parent
    if not oss_fuzz_root.exists():
        raise FileNotFoundError(f"OSS-Fuzz root does not exist: {oss_fuzz_root}")

    try:
        # Execute the build_fuzzers command using the venv Python
        print(f"Building fuzzers for project: {project}")
        
        print(f"Command: {sys.executable} infra/helper.py build_fuzzers {project}")
        
        result = subprocess.run([
            sys.executable,  # Use the current Python interpreter
            "infra/helper.py", 
            "build_fuzzers", 
            project,
            "--clean"
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
    
    # Path to the OSS-Fuzz root directory
    oss_fuzz_root = Path(repo_path).parent.parent

    # Get information about generated tests
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
                print(f"{fuzzer_name}: Unexpected error: {e}")
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


def print_tests_results(owner: str, name: str, get_all: bool = False, scanner_id: int = None):
    """
    Prints a summary of the test results for a given project using rich library.
    If get_all is True, it retrieves all scanner data, otherwise only the latest.
    If scanner_id is provided, it retrieves data for that specific scanner, if not, it retrieves the latest scanner.
    """
    
    repo_path = generate_path_repo(owner, name)

    if scanner_id:
        if get_all:
            scanner = get_scanner_all_data_by_id(scanner_id)
        else:
            scanner = get_scanner_by_id(scanner_id)
    else:
        if get_all:
            scanner = get_last_scanner_all_data_by_project(owner, name)
        else:
            scanner = get_last_scanner_data_by_project(owner, name)
    
    
    # Initialize variables to store items
    artifacts = set()
    fuzzers = set()
    
    
    console = Console()
    
    # Header
    title = f"Test results for project: {owner}/{name}"
    console.print(Panel(Align.center(title), border_style="blue"))
    
    # Table with vulnerabilities and their status
    vulnerabilities = Table(
        title="Vulnerabilities found",
        show_header=True,
        header_style="bold magenta",
        show_lines=True
    )
    vulnerabilities.add_column("Vulnerability")
    vulnerabilities.add_column("Impact")
    vulnerabilities.add_column("Attack vector")
    vulnerabilities.add_column("Status")
    vulnerabilities.add_column("Affected artifacts")
    
    for vulnerability in scanner.vulnerabilities:
        # Accumulate artifacts in set for later use
        for artifact in vulnerability.artifacts:
            artifacts.add(artifact)
            
        vulnerabilities.add_row(
            vulnerability.name,
            str(vulnerability.impact),
            vulnerability.attackVector,
            get_pretty_vulnerability_status(vulnerability.status),
            get_pretty_artifacts_names(vulnerability.artifacts)
        )

    # Table with artifacts and their status
    artifacts_table = Table(
        title="Artifacts Status",
        show_header=True,
        header_style="bold magenta",
        show_lines=True
    )
    artifacts_table.add_column("Artifact")
    artifacts_table.add_column("Line")
    artifacts_table.add_column("File Path")
    artifacts_table.add_column("Status")
    artifacts_table.add_column("Fuzzers")

    for artifact in artifacts:
        # Accumulate fuzzers in set for later use
        for fuzzer in artifact.fuzzers:
            fuzzers.add(fuzzer)
        
        # Remove repo part from path
        full_path = Path(artifact.filePath)
        relative_path = full_path.relative_to(repo_path)
        artifact_path = relative_path
        artifacts_table.add_row(
            artifact.name,
            str(artifact.line),
            str(artifact_path),
            get_pretty_vulnerability_status(artifact.affected),
            get_pretty_fuzzers_names(artifact.fuzzers)
        )
        
    # Table with fuzzers and informacion
    fuzzers_table = Table(
        title="Fuzzers Info",
        show_header=True,
        header_style="bold magenta",
        show_lines=True
    )
    
    fuzzers_table.add_column("Fuzzer name")
    fuzzers_table.add_column("Artifact tested")
    fuzzers_table.add_column("Line")
    fuzzers_table.add_column("File Path")
    fuzzers_table.add_column("Status")
    fuzzers_table.add_column("Crash type")
    fuzzers_table.add_column("Crash description")
    
    for fuzzer in fuzzers:
        fuzzers_table.add_row(
            fuzzer.name,
            fuzzer.artifactName,
            str(fuzzer.artifactLine),
            fuzzer.artifactPath,
            get_pretty_test_status(fuzzer.status),
            fuzzer.crashType,
            fuzzer.crashDescription
        )

    console.print(vulnerabilities)
    console.print()
    console.print(artifacts_table)
    console.print()
    console.print(fuzzers_table)
    
    
    
def get_pretty_vulnerability_status(status: VulnerabilityStatus) -> str:
    pretty_status = None
    if status == VulnerabilityStatus.AFFECTED:
        pretty_status = Text("Affected", style="bold red")
    elif status == VulnerabilityStatus.NOT_AFFECTED:
        pretty_status = Text("Not affected", style="bold green")
    else:
        pretty_status = Text("Unknown", style="dim")
    return pretty_status

def get_pretty_test_status(status: TestStatus) -> str:
    pretty_status = None
    if status == TestStatus.VULNERABLE:
        pretty_status = Text("Vulnerable", style="bold red")
    elif status == TestStatus.NOT_VULNERABLE:
        pretty_status = Text("Not vulnerable", style="bold green")
    elif status in [TestStatus.ERROR_BUILDING, TestStatus.ERROR_EXECUTING, TestStatus.ERROR_GENERATING]:
        pretty_status = Text(f"{status.value}", style="yellow")
    else:
        pretty_status = Text("Created", style="bold blue")
    return pretty_status

def get_pretty_artifacts_names(artifacts: list) -> str:
    pretty_artifact_names = Text()
    if not artifacts:
        pretty_artifact_names.append("No artifacts found", style="dim")
    else:
        for artifact in artifacts:
            if artifact.affected == VulnerabilityStatus.AFFECTED:
                pretty_artifact_names.append(f"{artifact.name} - {artifact.line}\n", style="bold red")
            elif artifact.affected == VulnerabilityStatus.NOT_AFFECTED:
                pretty_artifact_names.append(f"{artifact.name} - {artifact.line}\n", style="bold green")
            else:
                pretty_artifact_names.append(f"{artifact.name} - {artifact.line}\n", style="dim")
    return pretty_artifact_names

def get_pretty_fuzzers_names(fuzzers: list) -> str:
    pretty_fuzzer_names = Text()
    if not fuzzers:
        pretty_fuzzer_names.append("No fuzzers found", style="dim")
    else:
        for fuzzer in fuzzers:
            if fuzzer.status == TestStatus.VULNERABLE:
                pretty_fuzzer_names.append(f"{fuzzer.name}\n", style="bold red")
            elif fuzzer.status == TestStatus.NOT_VULNERABLE:
                pretty_fuzzer_names.append(f"{fuzzer.name}\n", style="bold green")
            elif fuzzer.status in [TestStatus.ERROR_BUILDING, TestStatus.ERROR_EXECUTING, TestStatus.ERROR_GENERATING]:
                pretty_fuzzer_names.append(f"{fuzzer.name}\n", style="yellow")
            else:
                pretty_fuzzer_names.append(f"{fuzzer.name}\n", style="dim")
    return pretty_fuzzer_names



def print_scanners(owner, name, scanner_list):
    """
    Prints the list of scanners for a given project.
    Input: owner of the repository, name of the repository and list of enumerate scanners (enumerate(scanner))
    """
    
    console = Console()
    
    # Header
    title = f"Scanner history for: {owner}/{name}"
    console.print(Panel(Align.center(title), border_style="blue"))
    
    # Table with vulnerabilities and their status
    scanners = Table(
        title="Scanners found",
        show_header=True,
        header_style="bold magenta",
        show_lines=True
    )
    scanners.add_column("Scanner")
    scanners.add_column("Date")
    scanners.add_column("Confidence level")

    for i, scanner in scanner_list:
        scanners.add_row(
            str(i) ,
            scanner.date.strftime("%Y-%m-%d %H:%M:%S"),
            str(scanner.confidence)
        )

    console.print(scanners)


def print_fuzzers_with_errors(owner: str, name: str, fuzzers: list) -> None:
    """Prints the list of fuzzers with errors for a given project.

    Keyword arguments:
    owner -- Owner of the repository
    name -- Name of the repository
    fuzzers -- List of enumerated (enumerate(list)) fuzzers with errors
    """
    
    console = Console()
    
    # Header
    title = f"Fuzzers with errors for: {owner}/{name}"
    console.print(Panel(Align.center(title), border_style="blue"))
    
    # Table with vulnerabilities and their status
    fuzzers_table = Table(
        title="Fuzzers Info",
        show_header=True,
        header_style="bold magenta",
        show_lines=True
    )
    fuzzers_table.add_column("Fuzzer")
    fuzzers_table.add_column("Fuzzer name")
    fuzzers_table.add_column("Line")
    fuzzers_table.add_column("File Path")
    fuzzers_table.add_column("Status")
    
    for i, fuzzer in fuzzers:
        fuzzers_table.add_row(
            str(i),
            fuzzer.artifactName,
            str(fuzzer.artifactLine),
            fuzzer.artifactPath,
            get_pretty_test_status(fuzzer.status)
        )
    console.print(fuzzers_table)