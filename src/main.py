import os
from java_analyzer.spoon_reader import get_artifact_info
from test_generator.generator import generate_fuzzer
from dotenv import load_dotenv
import typer
from vexgen_caller.auth import signup, login
from vexgen_caller.vex_generator import generate_vex, open_vex_file

load_dotenv()

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
    # TODO: add level of confidence
    ):
    """
    Generates vex and automatically runs tests.
    """
    artifacts_json = None
    # if not reload:
    #     try:
    #         artifacts_json = open_vex_file(owner, name)
    #         print(f"Using existing VEX file")
    #     except FileNotFoundError:
    #         print(f"VEX file not found, generating a new one...")
    #         generate_vex(owner, name, sbom_path)
    #         artifacts_json = open_vex_file(owner, name)
    # else:
    #     generate_vex(owner, name, sbom_path)
    #     artifacts_json = open_vex_file(owner, name)

    artifacts_json = """
    [
        {
            "file_path": "vulnerableCodeExamples/jacksonDatabind-CWE-502/src/main/java/com/example/JsonProcessor.java",
            "target_line": "24",
            "target_name": "readValue"
        }
    ]
    """
    
    # Generate artifacts info with Spoon
    artifacts_data = None
    if artifacts_json and artifacts_json != "[]":
        path = os.path.abspath(pom_path)
        artifacts_data = get_artifact_info(os.path.abspath(pom_path), artifacts_json)
    else:
        print("No artifacts found in the VEX file.")
        return
    
    
    if artifacts_data:
        for artifact in artifacts_data:
            # print(f"Processing artifact: {artifact.get('artifactData', {}).get('artifactName', 'Unknown')}")
            
            # Verificar que existe allCallPaths y tiene al menos un elemento
            all_call_paths = artifact.get("allCallPaths", [])
            if all_call_paths and len(all_call_paths) > 0 and len(all_call_paths[0]) > 1:
                entry_data = all_call_paths[0][1]
                
                generate_fuzzer(
                    data=entry_data,
                    # TODO: specify the output directory for generated fuzzers in production
                    exit_directory="generated_fuzzers"
                )
            else:
                # print(f"No valid call paths found for artifact: {artifact.get('artifactData', {}).get('artifactName', 'Unknown')}")
                print(f"No valid call paths found for artifact.")

if __name__ == "__main__":
    # app()
    run(
        owner="example-owner",
        name="example-repo", 
        sbom_path="path/to/sbom.json",
        pom_path="vulnerableCodeExamples/jacksonDatabind-CWE-502/pom.xml",
        reload=False
    )