import javalang
import argparse
from typing import Dict, Any, Optional

def open_java_file(file_path: str) -> javalang.tree.CompilationUnit:
    """Abre y parsea un archivo Java."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            code = file.read()
        return javalang.parse.parse(code)
    except FileNotFoundError:
        raise FileNotFoundError(f"El archivo {file_path} no existe.")
    except Exception as e:
        raise Exception(f"Error al parsear el archivo {file_path}: {e}")
        
        
def get_package_name(code_tree: javalang.tree.CompilationUnit) -> str:
    """Obtiene el nombre del paquete del archivo Java."""
    if code_tree and code_tree.package:
        return code_tree.package.name
    return ""

def get_imports(code_tree: javalang.tree.CompilationUnit) -> Dict[str, str]:
    """Obtiene un diccionario de imports: {nombre_clase: paquete_completo}."""
    imports = {}
    
    for imp in code_tree.imports:
        if imp.wildcard:
            # Para imports con *, guardar el paquete base con prefijo especial
            imports[f"{imp.path}"] = "*"
        else:
            # Import específico: com.example.MyClass
            full_path = imp.path
            class_name = full_path.split('.')[-1]
            package_path = '.'.join(full_path.split('.')[:-1])
            imports[class_name] = package_path
    
    return imports


def find_function_call_at_line(code_tree: javalang.tree.CompilationUnit, target_line: int, artifact_name: str) -> Optional[javalang.tree.MethodInvocation]:
    """Encuentra la llamada a método en la línea especificada.
    Tiene una salida tal que:
    {
        'target_method': MethodInvocation(
            arguments=[
            ArrayCreator(
                dimensions=[None],
                initializer=ArrayInitializer(initializers=[
                Literal(value=88)
                ]),
                type=BasicType(name=byte)
            )
            ],
            member='proceedInput', #Nombre del método
            qualifier='vulnerable' # Nombre del objeto desde el que se llama al método, en este ejemplo 'vulnerable.proceedInput...
                                   # No indica el tipo de objeto, ni si es método estático o no.
        )
        }
    """
    
    target_call = None
    closest_line_diff = float('inf')
    
    for path, node in code_tree.filter(javalang.tree.MethodInvocation):
        if hasattr(node, 'position') and node.position and node.member == artifact_name:
            line_diff = abs(node.position.line - target_line)
            if node.position.line <= target_line and line_diff < closest_line_diff:
                target_call = node
                closest_line_diff = line_diff
    
    return target_call


def analyze_java_file_v2(file_path: str, line_num: int, artifact_name: str) -> Optional[Dict[str, Any]]:
    try:
        code_tree = open_java_file(file_path)
        
        imports = get_imports(code_tree)
        
        package_name = get_package_name(code_tree)

        target_function = find_function_call_at_line(code_tree, line_num, artifact_name)
        
        function_data = {
            # "target_package":  package_name,
            "target_method": target_function,
            "imports": imports
        }
        
        return function_data
        
    except Exception as e:
        raise Exception(f"Ocurrió un error al analizar el fichero: {e}")
            


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
