import os
from pathlib import Path
from java_analyzer.spoon_reader import get_artifact_info
from test_generator.generator import generate_fuzzer
from dotenv import load_dotenv
import typer
from vexgen_caller.auth import signup, login
from vexgen_caller.vex_generator import generate_vex, open_tix_file
from utils.file_writer import resolve_path, generate_path_repo, write_test_info_to_json
from utils.git_utils import clone_repo
from utils.classes import TestStatus, TestInfo, ConfidenceLevel
from autofuzz.autofuzz import build_tests, execute_tests

load_dotenv()

# Definir rutas base del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
OSS_FUZZ_PROJECTS_ROOT = PROJECT_ROOT / "OSS-Fuzz" / "projects"
# Just to test with a known vulnerable example
VULNERABLE_EXAMPLES_ROOT = PROJECT_ROOT / "vulnerableCodeExamples"

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
    
    print(f"Resolved POM path: {resolved_pom_path}")
    
    # Verificar que los archivos existen
    if not resolved_pom_path.exists():
        raise FileNotFoundError(f"Error: POM file not found at {resolved_pom_path}")

    
    artifacts_json = None
    if not reload:
        try:
            artifacts_json = open_tix_file(owner, name)
            print(f"Using existing TIX file")
        except FileNotFoundError:
            print(f"TIX file not found, generating a new one...")
            generate_vex(owner, name)
            artifacts_json = open_tix_file(owner, name)
    else:
        generate_vex(owner, name)
        artifacts_json = open_tix_file(owner, name)

    artifacts_json = f"""
    [
        {{
            "file_path": "{dest_path / 'src' / 'main' / 'java' / 'com' / 'example' / 'JsonProcessor.java'}",
            "target_line": "24",
            "target_name": "readValue"
        }}
    ]
    """
    
    # Generate artifacts info with Spoon
    artifacts_data = None
    if artifacts_json and artifacts_json != "[]":
        artifacts_data = get_artifact_info(str(resolved_pom_path), artifacts_json)
    else:
        print("No artifacts found in the VEX file.")
        return
    
    if artifacts_data:
        # Definir directorio de salida dentro del proyecto clonado
        test_dir = dest_path / "src" / "test" / "java"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Dict to store test results
        test_results = {}
        test_already_generated = set()
        for artifact in artifacts_data:
            all_call_paths = artifact.get("allCallPaths", [])
            artifact_data = artifact.get("artifactData")
            artifact_key = f"{artifact_data.get('className')}_{artifact_data.get('artifactName')}_{artifact_data.get('lineNumber')}"
            
            # One entry per artifact
            test_results[artifact_key] = {"vulnerable": "Not tested", "tests": []}
            
            if all_call_paths and len(all_call_paths) > 0:
                for call_path in all_call_paths:
                    
                    # For ech call path, store the generated tests
                    call_path_tests = []
                    for i in range(len(call_path) - 1, -1, -1):
                        print(f"Call path {i}: {call_path[i]}")
                        entry_data = call_path[i]
                        try:
                            test = generate_fuzzer(
                                data=entry_data,
                                exit_directory=str(test_dir)
                            )
                            test_info = TestInfo(str(test), TestStatus.CREATED).to_dict()
                            
                        except Exception as e:
                            print(f"Error generating fuzzer: {e}")
                            test_info = TestInfo("", TestStatus.ERROR_GENERATING)
                            # TODO: add generic template 
                        
                        # Only add if not already generated
                        if test_info["test_path"] not in test_already_generated:
                            test_already_generated.add(test_info["test_path"])
                            call_path_tests.append(test_info)
                    test_results[artifact_key]["tests"].append(call_path_tests)
            else:
                print(f"No valid call paths found for artifact.")
        write_test_info_to_json(owner, name, test_results)
        
                
    # Exectute fuzz tests
    build_tests(owner, name)
    execute_tests(owner, name) 
     
     
     
     
     
     
     
     
     
     
                
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
        reload=True
    )
    
    # securechaindev / vex_generation_test 
    # TFG-josrodlop19 / VulnerableProject1