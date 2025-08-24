import subprocess
import json
import os

def get_artifact_info(pom_path: str, artifacts_data: str) -> dict:
    """
    Executes the Java analyzer to get information about a specific artifact in a Java file.
    """
    analyzer_jar_path = "java-analyzer/target/java-analyzer-1.0-SNAPSHOT-jar-with-dependencies.jar"
    
    command = [
        "java",
        "-jar",
        analyzer_jar_path,
        pom_path,   
        artifacts_data
    ]
    
    print(f"Executing: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error while analyzing file: {e}")
        print("--- Spoon stdout ---")
        print(e.stdout)
        print("--- Spoon stderr ---")
        print(e.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON output: {e}")
        print("--- Raw output ---")
        print(result.stdout)
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None