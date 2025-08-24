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
def vexgex_signup(
    email: str = typer.Argument(..., help="Email for the VEXGen account."),
    password: str = typer.Argument(..., help="Password for the VEXGen account.")
    ):
    signup(email, password)

@app.command()
def vexgen_login(
    email: str = typer.Argument(..., help="Email for the VEXGen account."),
    password: str = typer.Argument(..., help="Password for the VEXGen account.")
    ):
    login(email, password)
    
@app.command()
def run(
    owner : str = typer.Argument(..., help="Owner of the GitHub repository where the sbom.json file is stored."),
    name : str = typer.Argument(..., help="Name of the GitHub repository where the sbom.json file is stored."),
    sbom_path : str = typer.Argument("sbom.json", help="Path to the sbom.json file in the GitHub repository."),
    pom_path: str = typer.Argument(..., help="Path to the pom.xml file of the Maven project."),
    reload: bool = typer.Option(False, "--reload", "-r", help="Force re-generation of the VEX file even if it already exists.")
    ):
    """
    Run the VEXGen tool.
    """
    artifacts_json = None
    if not reload:
        try:
            artifacts_json = open_vex_file(owner, name)
            print(f"Using existing VEX file")
        except FileNotFoundError:
            print(f"VEX file not found, generating a new one...")
            generate_vex(owner, name, sbom_path, pom_path)
            artifacts_json = open_vex_file(owner, name)
    else:
        generate_vex(owner, name, sbom_path, pom_path)
        artifacts_json = open_vex_file(owner, name)
        
    # Generate artifacts info with Spoon
    artifacts_data = get_artifact_info(os.path.abspath(pom_path), artifacts_json)
    
    for artifact in artifacts_data:
        entry_data = artifact.get("allCallPaths")[0][1]

        generate_fuzzer(
            data=entry_data,
            # TODO: espcify the output directory for generated fuzzers in production
            exit_directory="fuzzers_generados"
        )

if __name__ == "__main__":
    app()
    # parser = argparse.ArgumentParser(description="Generates fuzzer tests for Maven projects.")
    # parser.add_argument("--pom_path", type=str, help="Path to the pom.xml file of the Maven project.")
    # parser.add_argument("--file_path", type=str, help="Path to java file containing the vulnerable code.")
    # parser.add_argument("--line_num", type=int, help="Número de línea donde se declara la función.")
    # parser.add_argument("--artifact_name", type=str, help="Name of the artifact to analyze.")
    # args = parser.parse_args()
    
    # # Analyze Java file to get information about the function
    # function_info = get_artifact_info(
    #     pom_path=args.pom_path,
    #     file_path=args.file_path,
    #     line_number=args.line_num,
    #     artifact_name=args.artifact_name
    # )
    
    # function_info = get_artifact_info(
        # pom_path="vulnerableCodeExamples/jacksonDatabind-CWE-502",
        # file_path="vulnerableCodeExamples/jacksonDatabind-CWE-502/src/main/java/com/example/JsonProcessor.java",
        # line_number=24,
        # artifact_name="readValue"
    # )
    # for artifact in function_info:
        # entry_data = artifact.get("allCallPaths")[0][1]
# 
    # generate_fuzzer(
        # data=entry_data,
        # TODO: espcify the output directory for generated fuzzers in production
        # exit_directory="fuzzers_generados"
    # )