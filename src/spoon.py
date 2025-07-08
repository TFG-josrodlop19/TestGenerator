import subprocess
import json
import os

def get_artifact_info(file_path: str, line_number: int, artifact_name: str) -> dict:
    """
    Ejecuta el analizador Spoon para un artefacto específico.
    """
    analyzer_jar_path = "java-analyzer/target/java-analyzer-1.0-SNAPSHOT-jar-with-dependencies.jar"
    
    command = [
        "java",
        "-jar",
        analyzer_jar_path,
        os.path.abspath(file_path),
        str(line_number),
        artifact_name
    ]
    
    print(f"Ejecutando: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error al analizar el artefacto: {e}")
        # Si hubo un error en el subproceso, imprime su salida de error
        if hasattr(e, 'stderr'):
            print("--- Salida de Error de Spoon ---")
            print(e.stderr)
        return None


# --- Ejemplo de uso ---
if __name__ == "__main__":
    # Analizamos la llamada a 'processInput' en la línea 10 del fichero especificado
    info = get_artifact_info("vulnerableCodeExamples/individualExamples/VulnerableCodeCall.java", 10, "processInput")

    if info:
        print("\n--- Información del Artefacto Encontrado ---")
        print(json.dumps(info, indent=2))