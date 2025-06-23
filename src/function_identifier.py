import javalang
import argparse
from typing import Dict, Any, Optional

def open_java_file(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            code = file.read()
        return javalang.parse.parse(code)
    except FileNotFoundError:
        print(f"Error: El fichero '{file_path}' no existe.")
        
        
def get_package_name(code_tree: javalang.tree.CompilationUnit) -> str:
    # Get the package of the Java file that contains the target function call
    # TODO: In a future version the package will be the one of the funtion definition
    name = ""
    if code_tree.package:
        name = code_tree.package.name
    return name


def analyze_java_file(file_path: str, line_num: int) -> Optional[Dict[str, Any]]:
    target_function = None
    container_class = None
    
    try:
        code_tree = open_java_file(file_path)
        
        package_name = get_package_name(code_tree)
        
        for _, class_node in code_tree.filter(javalang.tree.ClassDeclaration):
            possible_method = None
            possible_method_line = -1

            for _, node_method in class_node.filter(javalang.tree.MethodDeclaration):
                # La posición del nodo es la línea donde empieza la declaración del método
                start_method_line = node_method.position.line

                # Queremos el último método que empiece ANTES o EN la línea que nos interesa.
                # Esta es una heurística muy fiable para encontrar el método.
                if start_method_line <= line_num and start_method_line > possible_method_line:
                    possible_method = node_method
                    possible_method_line = start_method_line
            
            # Si encontramos un método candidato dentro de esta clase, es nuestro objetivo.
            if possible_method:
                target_function = possible_method
                container_class = class_node
                break # Salimos del bucle de clases

        if not target_function or not container_class:
            return None

        # Extraer toda la información relevante del método encontrado
        is_static = 'static' in target_function.modifiers
        params = [
            {"type": param.type.name, "name": param.name}
            for param in target_function.parameters
        ]

        return {
            "target_package": package_name,
            "target_class": container_class.name,
            "target_method": target_function.name,
            "is_static": is_static,
            "params": params,
            "line_of_declaration": target_function.position.line,
        }
    except Exception as e:
        print(f"Ocurrió un error al analizar el fichero: {e}")
        return None


# --- Punto de Entrada para ejecutar desde la línea de comandos ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detecta una función Java por fichero y línea.")
    parser.add_argument("--fichero", required=True, help="Ruta al fichero .java a analizar.")
    parser.add_argument("--linea", required=True, type=int, help="Número de línea dentro de la función objetivo.")
    
    args = parser.parse_args()

    info_funcion = analyze_java_file(args.fichero, args.linea)

    if info_funcion:
        print("¡Función detectada exitosamente!")
        print("---------------------------------")
        for clave, valor in info_funcion.items():
            print(f"{clave}: {valor}")
        print("---------------------------------")