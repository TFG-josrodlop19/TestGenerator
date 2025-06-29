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
                print(path)
        
    return target_call


def infer_parent_object_type(tree: javalang.tree.CompilationUnit, variable: str) -> str:
    """
    Recorre el AST y devuelve un diccionario de variables declaradas y sus tipos.
    Ejemplo: {'vulnerable': 'VulnerableCode'}
    """
    object_type = None
    for path, node in tree.filter(javalang.tree.VariableDeclaration):
        for declarator in node.declarators:
            if hasattr(declarator, 'name') and declarator.name == variable:
                object_type = node.type.name if hasattr(node, 'type') else None      
    return object_type


def analyze_java_file_v2(file_path: str, line_num: int, artifact_name: str) -> Optional[Dict[str, Any]]:
    try:
        code_tree = open_java_file(file_path)
        
        imports = get_imports(code_tree)

        target_function = find_function_call_at_line(code_tree, line_num, artifact_name)
        types = infer_parent_object_type(code_tree, target_function.qualifier) if target_function else None
              
        function_data = {
            # "target_package":  package_name,
            "target_function": target_function,
            "imports": imports,
            "types": types,
        }
        return function_data
    except Exception as e:
        raise Exception(f"Ocurrió un error al analizar el fichero: {e}")
            
