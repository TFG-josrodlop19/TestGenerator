import os
from pathlib import Path
from java_analyzer.spoon_reader import get_artifact_info
from test_generator.generator import generate_fuzzer
from dotenv import load_dotenv
import typer
from vexgen_caller.auth import signup, login
from vexgen_caller.vex_generator import generate_vex, open_vex_file
from utils.file_writer import resolve_path, generate_path_repo
from utils.git_utils import clone_repo

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
    sbom_path : str = typer.Argument(..., help="Path to the sbom.json file in the GitHub repository."),
    pom_path: str = typer.Argument(..., help="Path to the pom.xml file of the Maven project."),
    reload: bool = typer.Option(False, "--reload", "-r", help="Force re-generation of the VEX file even if it already exists.")
    # confidence
    ):
    """
    Generates vex and automatically runs tests.`
    """
    dest_path = Path(generate_path_repo(owner, name))
    # clone_repo(owner, name, dest_path)

    resolved_pom_path = resolve_path(pom_path, dest_path)
    resolved_sbom_path = resolve_path(sbom_path, dest_path)
    
    # Verificar que los archivos existen
    if not resolved_pom_path.exists():
        raise FileNotFoundError(f"Error: POM file not found at {resolved_pom_path}")

    if not resolved_sbom_path.exists():
        raise FileNotFoundError(f"Error: SBOM file not found at {resolved_sbom_path}")


    
    artifacts_json = None
    # if not reload:
    #     try:
    #         artifacts_json = open_vex_file(owner, name)
    #         print(f"Using existing VEX file")
    #     except FileNotFoundError:
    #         print(f"VEX file not found, generating a new one...")
    #         generate_vex(owner, name, str(resolved_sbom_path))
    #         artifacts_json = open_vex_file(owner, name)
    # else:
    #     generate_vex(owner, name, str(resolved_sbom_path))
    #     artifacts_json = open_vex_file(owner, name)

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
        # print(artifacts_data)
    else:
        print("No artifacts found in the VEX file.")
        return
    
    if artifacts_data:
        for artifact in artifacts_data:
            all_call_paths = artifact.get("allCallPaths", [])
            if all_call_paths and len(all_call_paths) > 0 and len(all_call_paths[0]) > 1:
                entry_data = all_call_paths[0][1]
                
                # Definir directorio de salida dentro del proyecto clonado
                test_dir = dest_path / "src" / "test" / "java"
                test_dir.mkdir(parents=True, exist_ok=True)
                
                generate_fuzzer(
                    data=entry_data,
                    exit_directory=str(test_dir)
                )
            else:
                print(f"No valid call paths found for artifact.")
                
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
    current_dir = Path.cwd()
    autofuzz_dir = current_dir / ".autofuzz"
    
    # Verificar si ya existe
    if autofuzz_dir.exists() and not force:
        print(f"Directory .autofuzz already exists at {autofuzz_dir}")
        print("Use --force to overwrite existing structure")
        return
    
    try:
        # Crear el directorio .autofuzz
        autofuzz_dir.mkdir(exist_ok=force)
        print(f"Successfully created .autofuzz directory at {autofuzz_dir}")
        
        # Crear build.sh
        build_sh_content = """#!/bin/bash
            # Build script for OSS-Fuzz fuzzing
            # Add your build commands here
            """
        (autofuzz_dir / "build.sh").write_text(build_sh_content)
        
        # Crear Dockerfile
        dockerfile_content = """# Dockerfile for OSS-Fuzz
            # Add your Docker configuration here

            """
        (autofuzz_dir / "Dockerfile").write_text(dockerfile_content)
        
        # Crear project.yaml
        project_yaml_content = """# Project configuration for OSS-Fuzz
            # Add your project configuration here

            """
        (autofuzz_dir / "project.yaml").write_text(project_yaml_content)
        
        print("Created OSS-Fuzz configuration files:")
        print(f"  - {autofuzz_dir / 'build.sh'}")
        print(f"  - {autofuzz_dir / 'Dockerfile'}")
        print(f"  - {autofuzz_dir / 'project.yaml'}")
        
    except Exception as e:
        print(f"Error creating .autofuzz directory: {e}")
        raise typer.Exit(1)
    

if __name__ == "__main__":
    app()
    # run(
    #     owner="TFG-josrodlop19",
    #     name="VulnerableProject1", 
    #     sbom_path="sbom.json",  # Ruta relativa desde PROJECT_ROOT
    #     pom_path="pom.xml",     # Ruta relativa desde PROJECT_ROOT
    #     reload=False
    # )