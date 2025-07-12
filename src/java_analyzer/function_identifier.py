import javalang
from typing import Dict, Any, Optional, List
from utils.classes import FunctionInfo, NodeInfo
from collections import namedtuple
from java_analyzer.aux import open_java_file
        
        
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
    target_call = None
    closest_line_diff = float('inf')
    
    for path, node in code_tree.filter(javalang.tree.MethodInvocation):
        if hasattr(node, 'position') and node.position and node.member == artifact_name:
            line_diff = abs(node.position.line - target_line)
            if node.position.line <= target_line and line_diff < closest_line_diff:
                target_call = NodeInfo(path, node)
                closest_line_diff = line_diff
    return target_call

def _get_node_type_if_qualifier(node: javalang.tree.Node, qualifier: str) -> str:
    if isinstance(node, javalang.tree.MethodDeclaration):
        for parameter in node.parameters:
            if parameter.name == qualifier:
                # TODO: implement a function to properly get the type in case of [] or other complex types
                return parameter.type.name
    # Check if the variable is declared as a local variable in a block of statements        
    if isinstance(node, javalang.tree.LocalVariableDeclaration):
        for declarator in node.declarators:
            if declarator.name == qualifier:
                return declarator.initializer.type.name
    # Buscar como variable local en cualquier bloque de sentencias
    # (cuerpos de métodos, bucles for, bloques if, etc.)
    if hasattr(node, 'statements'):
        for statement in node.statements:
            if isinstance(statement, javalang.tree.LocalVariableDeclaration):
                for declarator in statement.declarators:
                    if declarator.name == qualifier:
                        return declarator.initializer.type.name 
    # Buscar como campo (atributo) de la clase
    if isinstance(node, javalang.tree.ClassDeclaration):
        for field in node.body:
            if isinstance(field, javalang.tree.FieldDeclaration):
                for declarator in field.declarators:
                    if declarator.name == qualifier:
                        return field.type.name
    return None

# TODO: look out the other vulnerable code to see how works a method implementation and call in the same class
# TODO: currently it does not look in every branch of the node path, only in parents nodes and their children
def _get_qualifier_type(node_path: List[javalang.tree.Node], qualifier: str):
    nodes_already_visited = set()
    for node_not_normalized in reversed(node_path):
        # Normalize nodes into a list if it's not already
        nodes_to_check = node_not_normalized if isinstance(node_not_normalized, list) else [node_not_normalized]
        for node in filter(lambda n: n not in nodes_already_visited, nodes_to_check):        
            # Check if the variable is declared as a parameter in a method
            object_type = _get_node_type_if_qualifier(node, qualifier)
            if object_type:
                return object_type
            nodes_already_visited.add(node)
    return None

# def recursiva(node_path: List[javalang.tree.Node], qualifier: str):
    

# TODO: esto seguro que se puede mover a la funcion anterior
def infer_parent_object_type(node_info: NodeInfo, imports: Dict[str, str]) -> str:
    # TODO: check this case
    # If there is no qualifier it means it is a local call. Example: `processInput()`
    qualifier = node_info.qualifier()
    if not node_info or not node_info.path or not qualifier:
        return False
    
    is_static = False
    
    function_node = node_info.node
    # Qualifier is the name of the object from which the method is called
    qualifier_type = _get_qualifier_type(node_info.path, qualifier)
    
    if not qualifier_type:
        # If the qualifier type is not found, it might be a static method call
        a = 3
         
    return {"qualifier_type": qualifier_type, "is_static": is_static}


def analyze_java_file(file_path: str, line_num: int, artifact_name: str) -> Optional[Dict[str, Any]]:
    try:
        code_tree = open_java_file(file_path)
        
        imports = get_imports(code_tree)

        target_function = find_function_call_at_line(code_tree, line_num, artifact_name)       
        # Later it will be needed to check imports to determine which one to return
        types = infer_parent_object_type(target_function, imports)
              
        function_data = {
            # "target_package":  package_name,
            "target_function": target_function,
            "imports": imports,
            "types": types,
        }
        return function_data
    except Exception as e:
        raise Exception(f"Ocurrió un error al analizar el fichero: {e}")
            
