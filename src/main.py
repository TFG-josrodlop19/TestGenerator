from java_analyzer.spoon_reader import get_artifact_info
from test_generator.generator import generate_fuzzer
import argparse

if __name__ == "__main__":
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
    
    function_info = get_artifact_info(
        pom_path="vulnerableCodeExamples/jacksonDatabind-CWE-502",
        file_path="vulnerableCodeExamples/jacksonDatabind-CWE-502/src/main/java/com/example/JsonProcessor.java",
        line_number=23,
        artifact_name="readValue"
    )
    entry_data = function_info.get("allCallPaths")[0][0]

    generate_fuzzer(
        data=entry_data,
        # TODO: espcify the output directory for generated fuzzers in production
        exit_directory="fuzzers_generados"
    )