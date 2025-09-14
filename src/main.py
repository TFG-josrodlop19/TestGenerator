import os
from pathlib import Path
from java_analyzer.spoon_reader import get_artifact_info
from test_generator.generator import generate_fuzzers
from dotenv import load_dotenv
import typer
from vexgen_caller.auth import signup, login
from vexgen_caller.vex_generator import generate_vex, get_tix_data
from utils.file_writer import resolve_path, generate_path_repo, write_test_info_to_json
from utils.git_utils import clone_repo
from autofuzz.autofuzz import build_tests, execute_tests
from database.models import ConfidenceLevel

from database.setup import setup_database
from database.operations import create_project, create_vulnerabilities_artifacts

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
    reload: bool = typer.Option(False, "--reload", "-r", help="Force re-generation of the VEX file even if it already exists."),
    confidence: ConfidenceLevel = typer.Option(
        ConfidenceLevel.MEDIUM, 
        "--confidence", 
        "-c", 
        help="Confidence level for test execution. Low: 2 min, Medium: 10 min, High: 1 hour, Absolute: unlimited."
    )
    ):
    """
    Generates vex and automatically runs tests.`
    """
    dest_path = Path(generate_path_repo(owner, name))
    clone_repo(owner, name, dest_path)
    
    print(f"Cloned repository to: {dest_path}")

    resolved_pom_path = resolve_path(pom_path, dest_path)

        
    # Verificar que los archivos existen
    if not resolved_pom_path.exists():
        raise FileNotFoundError(f"Error: POM file not found at {resolved_pom_path}")

    # TODO: quitar luego confidence de aqui
    confidence = ConfidenceLevel.MEDIUM
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
        raise ValueError("No vulnerabilities found in the TIX file.")

    # This function also returns the scanner_id to use after in test generation
    create_vulnerabilities_artifacts(project.id, vulnerabilities)

    # artifacts_json = f"""
    # [
    #     {{
    #         "file_path": "{dest_path / 'src' / 'main' / 'java' / 'com' / 'example' / 'JsonProcessor.java'}",
    #         "target_line": "24",
    #         "target_name": "readValue"
    #     }}
    # ]
    # """
    
    # Generate artifacts info with Spoon
    artifacts_data = None
    if artifacts_json and artifacts_json != "[]":
        print(f"Artifacts JSON: {artifacts_json}")
        
        artifacts_data = get_artifact_info(str(resolved_pom_path), artifacts_json)
    else:
        print("No artifacts found in the VEX file.")
        return
    
    if artifacts_data:
        generate_fuzzers(owner, name, artifacts_data)
               
        # Exectute fuzz tests
        build_tests(owner, name)
        # execute_tests(owner, name) 
     
     
     
     
     
     
     
     
     
     
                
def repair_tests(
    owner : str = typer.Argument(..., help="Owner of the GitHub repository where the sbom.json file is stored."),
    name : str = typer.Argument(..., help="Name of the GitHub repository where the sbom.json file is stored."),
):
    """
    Repairs the generated tests.
    """
    pass

@app.command()
def init(
    force : bool = typer.Option(False, "--force", "-f", help="Force re-initialization even if the structure already exists.")
    ):
    """
    Initializes the project structure.
    """
    # Obtener el directorio actual desde donde se invoca el comando
    file_paths = Path.cwd()
    

    
    try:
        # Crear el directorio .autofuzz
        file_paths.mkdir(exist_ok=force)
        print(f"Successfully created .autofuzz directory at {file_paths}")

        # Crear build.sh
        build_sh_content = """#!/bin/bash
            # Build script for OSS-Fuzz fuzzing
            # Add your build commands here
            """
        (file_paths / "build.sh").write_text(build_sh_content)

        # Crear Dockerfile
        dockerfile_content = """# Dockerfile for OSS-Fuzz
            # Add your Docker configuration here

            """
        (file_paths / "Dockerfile").write_text(dockerfile_content)

        # Crear project.yaml
        project_yaml_content = """# Project configuration for OSS-Fuzz
            # Add your project configuration here

            """
        (file_paths / "project.yaml").write_text(project_yaml_content)

        print("Created OSS-Fuzz configuration files:")
        print(f"  - {file_paths / 'build.sh'}")
        print(f"  - {file_paths / 'Dockerfile'}")
        print(f"  - {file_paths / 'project.yaml'}")
        
    except Exception as e:
        print(f"Error creating .autofuzz directory: {e}")
        raise typer.Exit(1)
    

if __name__ == "__main__":
    # app()
    run(
        owner="TFG-josrodlop19",
        name="VulnerableProject1", 
        pom_path="pom.xml",
        reload=False
    )
    
    # securechaindev / vex_generation_test 
    # TFG-josrodlop19 / VulnerableProject1