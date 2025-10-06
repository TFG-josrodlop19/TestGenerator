import shutil
from pathlib import Path
from dotenv import load_dotenv
import typer
from vexgen_caller.auth import signup, login
from autofuzz.autofuzz import generate_fuzz_tests, build_tests, execute_tests, print_tests_results, print_scanners, print_fuzzers_with_errors
from database.models import ConfidenceLevel, TestStatus
from database.setup import setup_database
from database.operations import find_last_scanner_confidence, update_fuzzer_status, update_states_after_execution, get_scanners_by_project, find_fuzzers_with_errors
import subprocess

load_dotenv()

setup_database()

PROJECT_ROOT = Path(__file__).parent.parent
OSS_FUZZ_PROJECTS_ROOT = PROJECT_ROOT / "OSS-Fuzz" / "projects"

app = typer.Typer()

@app.command()
def vexgen_signup(
    email: str = typer.Argument(..., help="Email for the VEXGen account.")
    ):
    """
    Signs up to Vexgen
    """
    password = typer.prompt("Password", hide_input=True, confirmation_prompt=True)
    signup(email, password)

@app.command()
def vexgen_login(
    email: str = typer.Argument(..., help="Email for the VEXGen account.")
    ):
    """
    Logs in to Vexgen
    """
    password = typer.prompt("Password", hide_input=True)
    login(email, password)
     
    
@app.command()
def run(
    owner : str = typer.Argument(..., help="Owner of the GitHub repository where the sbom.json file is stored."),
    name : str = typer.Argument(..., help="Name of the GitHub repository where the sbom.json file is stored."),
    pom_path: str = typer.Argument(..., help="Path to the pom.xml file of the Maven project."),
    reload: bool = typer.Option(True, "--no-reload", "-n", help="Do not re-generate TIX file if it already exists."),
    confidence: ConfidenceLevel = typer.Option(
        ConfidenceLevel.MEDIUM, 
        "--confidence", 
        "-c", 
        help="Confidence level for test execution. Low: 2 min, Medium: 10 min, High: 1 hour, Absolute: unlimited."
    )
    ):
    """
    Generates vex and automatically runs tests.
    """
    if generate_fuzz_tests(owner, name, pom_path, confidence, reload):
        # Execute fuzz tests
        build_tests(owner, name)
        execute_tests(owner, name, confidence)
        update_states_after_execution(owner, name)
        print_tests_results(owner, name)
        
@app.command()
def generate(
    
    owner : str = typer.Argument(..., help="Owner of the GitHub repository where the sbom.json file is stored."),
    name : str = typer.Argument(..., help="Name of the GitHub repository where the sbom.json file is stored."),
    pom_path: str = typer.Argument(..., help="Path to the pom.xml file of the Maven project."),
    reload: bool = typer.Option(True, "--no-reload", "-n", help="Do not re-generate TIX file if it already exists."),
    confidence: ConfidenceLevel = typer.Option(
        ConfidenceLevel.MEDIUM, 
        "--confidence", 
        "-c", 
        help="Confidence level for test execution. Low: 2 min, Medium: 10 min, High: 1 hour, Absolute: unlimited."
    )
    ):
    """
    Generates the VEX file and the tests for a given project.
    """
    generate_fuzz_tests(owner, name, pom_path, confidence, reload)
    
    
@app.command()
def runtests(
    owner : str = typer.Argument(..., help="Owner of the GitHub repository where the sbom.json file is stored."),
    name : str = typer.Argument(..., help="Name of the GitHub repository where the sbom.json file is stored.")
    ):
    """
    Re-builds and runs the tests for a given project (last scanner).
    """
    confidence = find_last_scanner_confidence(owner, name)
    build_tests(owner, name)
    execute_tests(owner, name, confidence)
    update_states_after_execution(owner, name)
    print_tests_results(owner, name)

@app.command()
def scanners(
        owner : str = typer.Argument(..., help="Owner of the GitHub repository where the sbom.json file is stored."),
        name : str = typer.Argument(..., help="Name of the GitHub repository where the sbom.json file is stored."),
        limit : int = typer.Option(10, "--limit", "-l", help="Number of recent scanners to display (default: 10, -1 to list all)."),
        all : bool = typer.Option(False, "--all", "-a", help="Show all data for each scanner.")
    ):
    """
    Show the scanners for a given project and allows to view test results for a selected scanner.
    """
    
    scanners_list= get_scanners_by_project(owner, name, limit)

    if not scanners_list or len(scanners_list) == 0:
        print("No scanners found for this project.")
        return
    scanners = enumerate(scanners_list)
    print_scanners(owner, name, scanners)
         
    # Ask user to select a scanner
    try:
        while True:
            selection = typer.prompt(f"Enter the number of the scanner you want to view (0 - {len(scanners_list)-1})")
            selection = int(selection)
            if not (0 <= selection < len(scanners_list)):
                print("Invalid selection. Please enter a valid number.")
            else:
                break
        scanner = scanners_list[selection]
        print_tests_results(owner, name, all, scanner.id)

    except Exception as e:
        print(f"Error: {e}")
        return

@app.command()
def repair(
    owner : str = typer.Argument(..., help="Owner of the GitHub repository where the sbom.json file is stored."),
    name : str = typer.Argument(..., help="Name of the GitHub repository where the sbom.json file is stored."),
):
    """
    Repairs the generated tests.
    """
    fuzzers_list = find_fuzzers_with_errors(owner, name) 
    if not fuzzers_list or len(fuzzers_list) == 0:
        print("No fuzzers with errors found for this project.")
        return
    fuzzers = enumerate(fuzzers_list)
    print_fuzzers_with_errors(owner, name, fuzzers)
    
     # Ask user to select a fuzzer to repair
    try:
        while True:
            selection = typer.prompt(f"Enter the number of the fuzzer you want to repair (0 - {len(fuzzers_list)-1})")
            selection = int(selection)
            if not (0 <= selection < len(fuzzers_list)):
                print("Invalid selection. Please enter a valid number.")
            else:
                break
        fuzzer = fuzzers_list[selection]
        fuzzer_path = Path(fuzzer.testPath)

        if not fuzzer_path.exists():
            raise FileNotFoundError("Fuzzer file not found.")
        
        start_timestamp = fuzzer_path.stat().st_mtime
        res = subprocess.run(['vim', str(fuzzer_path)], capture_output=False)
        
        if res.returncode == 0:
            new_timestamp = fuzzer_path.stat().st_mtime
            if new_timestamp > start_timestamp:
                update_fuzzer_status(fuzzer.id, TestStatus.CREATED)
                print("Fuzzer modified, status updated")
            else:
                print("Fuzzer not modified, status not updated.")
        else:
            print("Vim exited with an error, status not updated.")   
    except Exception as e:
        print(f"Error: {e}")
        return

@app.command()
def init():
    """
    Initializes the project structure.
    """
    # Get current working directory
    current_dir = Path.cwd()

    templates_dir = PROJECT_ROOT / "templates"
    
    if not templates_dir.exists():
        raise FileNotFoundError(f"Error: Templates directory not found at {templates_dir}")
    
    try:
        files_to_copy = ["build.sh", "Dockerfile", "project.yaml"]
        for file in files_to_copy:
            template_path = templates_dir / file
            dest_path = current_dir / file
            if not template_path.exists():
                raise FileNotFoundError(f"Error: Template file {file} not found in {templates_dir}")
            if dest_path.exists():
                print(f"File {file} already exists at {dest_path}. Creating copy-{file} instead.")
                dest_path = current_dir / f"copy-{file}"
            shutil.copy2(template_path, dest_path)
            if dest_path.name.endswith("build.sh"):
                dest_path.chmod(0o755)
        print("Project structure initialized successfully.")
    except Exception as e:
        print(f"Error initializing project structure: {e}")
        raise typer.Exit(1)
    

if __name__ == "__main__":
    app()