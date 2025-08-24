import os
from pathlib import Path
from java_analyzer.spoon_reader import get_artifact_info
from test_generator.generator import generate_fuzzer
from dotenv import load_dotenv
import typer
from vexgen_caller.auth import signup, login
from vexgen_caller.vex_generator import generate_vex, open_vex_file

load_dotenv()

# Definir rutas base del proyecto
PROJECT_ROOT = Path(__file__).parent.parent  # /home/josue/universidad/TFG/TestGenerator
SRC_ROOT = Path(__file__).parent              # /home/josue/universidad/TFG/TestGenerator/src
VULNERABLE_EXAMPLES_ROOT = PROJECT_ROOT / "vulnerableCodeExamples"

app = typer.Typer()

def resolve_path(path: str) -> Path:
    """
    Resuelve una ruta relativa o absoluta y la convierte a Path absoluto.
    Si la ruta es relativa, la resuelve desde PROJECT_ROOT.
    """
    path_obj = Path(path)
    if path_obj.is_absolute():
        return path_obj
    else:
        # Si es relativa, probar primero desde PROJECT_ROOT
        project_path = PROJECT_ROOT / path
        if project_path.exists():
            return project_path.resolve()
        # Si no existe, probar desde el directorio actual
        current_path = Path.cwd() / path
        return current_path.resolve()

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
    ):
    """
    Generates vex and automatically runs tests.
    """
    
    # Resolver rutas usando la función helper
    resolved_pom_path = resolve_path(pom_path)
    resolved_sbom_path = resolve_path(sbom_path)
    
    print(f"Resolved POM path: {resolved_pom_path}")
    print(f"Resolved SBOM path: {resolved_sbom_path}")
    
    # Verificar que los archivos existen
    if not resolved_pom_path.exists():
        print(f"Error: POM file not found at {resolved_pom_path}")
        return
    
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
            "file_path": "{VULNERABLE_EXAMPLES_ROOT / 'jacksonDatabind-CWE-502' / 'src' / 'main' / 'java' / 'com' / 'example' / 'JsonProcessor.java'}",
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
        for artifact in artifacts_data:
            all_call_paths = artifact.get("allCallPaths", [])
            if all_call_paths and len(all_call_paths) > 0 and len(all_call_paths[0]) > 1:
                entry_data = all_call_paths[0][1]
                
                # Definir directorio de salida relativo al proyecto
                output_dir = PROJECT_ROOT / "generated_fuzzers"
                
                generate_fuzzer(
                    data=entry_data,
                    exit_directory=str(output_dir)
                )
            else:
                print(f"No valid call paths found for artifact.")

if __name__ == "__main__":
    # app()
    run(
        owner="example-owner",
        name="example-repo", 
        sbom_path="vulnerableCodeExamples/jacksonDatabind-CWE-502/sbom.json",  # Ruta relativa desde PROJECT_ROOT
        pom_path="vulnerableCodeExamples/jacksonDatabind-CWE-502/pom.xml",     # Ruta relativa desde PROJECT_ROOT
        reload=False
    )