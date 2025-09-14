import os
import shutil
import subprocess
import sys
from pathlib import Path
from utils.file_writer import generate_path_repo
from utils.classes import TestStatus
from database.operations import get_created_fuzzers_by_project, update_fuzzer_status, get_scanner_all_data_by_project
from database.models import Fuzzer, ConfidenceLevel, VulnerabilityStatus
import re
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich import box

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


def print_tests_results(owner: str, name: str, get_all: bool = False):
    #TODO: aplicar el get_all
    scanner = get_scanner_all_data_by_project(owner, name)

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
    vulnerabilities.add_column("CWEs")
    vulnerabilities.add_column("Status")
    vulnerabilities.add_column("Affected artifacts")

    # Contadores para estadísticas
    total = 0
    vulnerable = 0
    passed = 0
    errors = 0
    
    for vulnerability in scanner.vulnerabilities:
        
        # Get CWEs as a string
        cwe_list = [str(cwe.cwe_id) for cwe in vulnerability.cwes]
        cwe_str = "\n".join(cwe_list) if cwe_list else "N/A"
        
        vulnerabilities.add_row(
            vulnerability.name,
            cwe_str,
            get_pretty_vulnerability_status(vulnerability.status),
            get_pretty_artifacts_names(vulnerability.artifacts)
        )
    
    # for vulnerability in scanner.vulnerabilities:
    #     for artifact in vulnerability.artifacts:
    #         for fuzzer in artifact.fuzzers:
    #             total += 1
                
    #             # 🎨 ICONOS Y COLORES SEGÚN STATUS
    #             if fuzzer.status == TestStatus.VULNERABLE:
    #                 status_icon = "❌ VULNERABLE"
    #                 status_style = "bold red"
    #                 vulnerable += 1
    #                 vuln_info = fuzzer.crash_type or "Unknown"
    #             elif fuzzer.status == TestStatus.NOT_VULNERABLE:
    #                 status_icon = "✅ PASSED"
    #                 status_style = "bold green"
    #                 passed += 1
    #                 vuln_info = "None"
    #             elif fuzzer.status == TestStatus.ERROR_BUILDING:
    #                 status_icon = "🔨 BUILD ERROR"
    #                 status_style = "bold yellow"
    #                 errors += 1
    #                 vuln_info = "Compilation failed"
    #             elif fuzzer.status == TestStatus.ERROR_EXECUTING:
    #                 status_icon = "⚠️ EXEC ERROR"
    #                 status_style = "bold orange3"
    #                 errors += 1
    #                 vuln_info = "Runtime error"
    #             else:
    #                 status_icon = "⏳ PENDING"
    #                 status_style = "dim"
    #                 vuln_info = "Not executed"
                
    #             vulnerabilities.add_row(
    #                 fuzzer.name,
    #                 Text(status_icon, style=status_style),
    #                 fuzzer.crash_description[:40] + "..." if fuzzer.crash_description and len(fuzzer.crash_description) > 40 else (fuzzer.crash_description or ""),
    #                 vuln_info
    #             )
    
    console.print(vulnerabilities)
    
    # 📊 ESTADÍSTICAS FINALES
    stats_table = Table(title="📈 Summary Statistics", show_header=False)
    stats_table.add_column("Metric", style="bold")
    stats_table.add_column("Count", justify="right")
    stats_table.add_column("Percentage", justify="right")
    
    stats_table.add_row("🧪 Total Fuzzers", str(total), "100%")
    stats_table.add_row("✅ Passed", str(passed), f"{(passed/total*100):.1f}%" if total > 0 else "0%")
    stats_table.add_row("❌ Vulnerabilities Found", str(vulnerable), f"{(vulnerable/total*100):.1f}%" if total > 0 else "0%")
    stats_table.add_row("⚠️ Errors", str(errors), f"{(errors/total*100):.1f}%" if total > 0 else "0%")
    
    console.print()
    console.print(stats_table)
    
    # 🎯 RESULTADO FINAL
    if vulnerable > 0:
        result_style = "bold red"
        result_icon = "🚨"
        result_message = f"SECURITY ISSUES DETECTED! Found {vulnerable} vulnerable fuzzer(s)."
    elif errors > 0:
        result_style = "bold yellow"
        result_icon = "⚠️"
        result_message = f"COMPLETED WITH ERRORS. {errors} fuzzer(s) failed to execute properly."
    else:
        result_style = "bold green"
        result_icon = "🎉"
        result_message = "ALL TESTS PASSED! No vulnerabilities detected."
    
    console.print()
    console.print(Panel(
        Align.center(f"{result_icon} {result_message}"),
        border_style=result_style.split()[-1]  # Usar solo el color
    ))
    
    
def get_pretty_vulnerability_status(status: VulnerabilityStatus) -> str:
    pretty_status = None
    if status == VulnerabilityStatus.AFFECTED:
        pretty_status = Text("Affected", style="bold red")
    elif status == VulnerabilityStatus.NOT_AFFECTED:
        pretty_status = Text("Not affected", style="bold green")
    else:
        pretty_status = Text("Unknown", style="dim")
    return pretty_status

def get_pretty_artifacts_names(artifacts: list) -> str:
    pretty_artifact_names = Text()
    if not artifacts:
        pretty_artifact_names.append("No artifacts found", style="dim")
    else:
        for artifact in artifacts:
            if artifact.affected == VulnerabilityStatus.AFFECTED:
                pretty_artifact_names.append(f"{artifact.name}\n", style="bold red")
            elif artifact.affected == VulnerabilityStatus.NOT_AFFECTED:
                pretty_artifact_names.append(f"{artifact.name}\n", style="bold green")
            else:
                pretty_artifact_names.append(f"{artifact.name}\n", style="dim")
    return pretty_artifact_names