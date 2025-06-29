# Generate test cases for a given function
from src.test_generator.generator import generar_fuzzer_desde_plantilla
from src.java_analyzer.function_identifier import analyze_java_file
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera un fuzzer para una función Java específica.")
    parser.add_argument("--file_path", type=str, help="Ruta al archivo Java que contiene la función.")
    parser.add_argument("--line_num", type=int, help="Número de línea donde se declara la función.")
    
    args = parser.parse_args()
    
    # Analizar el archivo Java para obtener información de la función
    function_info = analyze_java_file(args.file_path, args.line_num)
    
    """
    target_package: com.example
    target_class: VulnerableCode
    target_method: processInput
    is_static: True
    # TODO: Maybe change to a namedtuple
    params: [{'type': 'byte', 'name': 'data'}]
    line_of_declaration: 14
    """
    
    context_parser = {
        "clase_fuzzer": function_info["target_class"] + "Fuzzer",
        "paquete_fuzzer": "com.example",
        "paquete_target": function_info["target_package"],
        "clase_target": function_info["target_class"],
        "metodo_target": function_info["target_method"],
        "params": function_info["params"]
    }
    
    
    generar_fuzzer_desde_plantilla(
        contexto=context_parser,
        directorio_salida="fuzzers_generados"
    )