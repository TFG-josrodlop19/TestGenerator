import subprocess
import json
import os
from pathlib import Path

def get_artifact_info(pom_path: str, artifacts_data: str) -> dict:
    """
    Executes the Java analyzer to get information about a specific artifact in a Java file.
    """
    # Ruta absoluta al JAR desde la ubicación de este archivo
    current_dir = Path(__file__).parent.parent.parent  # Subir 3 niveles para llegar a TestGenerator
    analyzer_jar_path = current_dir / "java-analyzer" / "target" / "java-analyzer-1.0-SNAPSHOT-jar-with-dependencies.jar"
    
    # Verificar que el JAR existe
    if not analyzer_jar_path.exists():
        print(f"Error: JAR not found at {analyzer_jar_path}")
        return None
    
    command = [
        "java",
        "-jar",
        str(analyzer_jar_path),  # Convertir Path a string
        pom_path,   
        artifacts_data
    ]
    
    print(f"Executing: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        
        # DEBUG información
        print(f"DEBUG - Return code: {result.returncode}")
        print(f"DEBUG - Stderr: {result.stderr}")
        print(f"DEBUG - Stdout: {result.stdout}")  # Mostrar stdout también
        
        if not result.stdout.strip():
            print("ERROR: stdout is empty!")
            return None
            
        parsed_data = json.loads(result.stdout)
        return parsed_data
        
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