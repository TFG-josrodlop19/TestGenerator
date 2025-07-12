import subprocess
import json
import os

def get_artifact_info(pom_path: str, file_path: str, line_number: int, artifact_name: str) -> dict:
    """
    Executes the Java analyzer to get information about a specific artifact in a Java file.
    """
    analyzer_jar_path = "java-analyzer/target/java-analyzer-1.0-SNAPSHOT-jar-with-dependencies.jar"
    
    command = [
        "java",
        "-jar",
        analyzer_jar_path,
        os.path.abspath(pom_path),
        os.path.abspath(file_path),
        str(line_number),
        artifact_name
    ]
    
    print(f"Executing: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error while analyzing file: {e}")
        if hasattr(e, 'stderr'):
            print("--- Spoon error ---")
            print(e.stderr)
        return None

if __name__ == "__main__":
    # Analizamos la llamada a 'processInput' en la línea 10 del fichero especificado
    info = get_artifact_info("vulnerableCodeExamples/jacksonDatabind-CWE-502","vulnerableCodeExamples/jacksonDatabind-CWE-502/src/main/java/com/example/JsonProcessor.java", 23, "readValue")

    if info:
        print("\n--- Información del Artefacto Encontrado ---")
        print(json.dumps(info, indent=2))