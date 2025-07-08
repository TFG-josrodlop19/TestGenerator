from javalang.tree import Node, CompilationUnit
from javalang import parse
from typing import List

def open_java_file(file_path: str) -> CompilationUnit:
    """Abre y parsea un archivo Java."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            code = file.read()
        return parse.parse(code)
    except FileNotFoundError:
        raise FileNotFoundError(f"El archivo {file_path} no existe.")
    except Exception as e:
        raise Exception(f"Error al parsear el archivo {file_path}: {e}")

def next_node_in_path_from_leaf(node_path: List[Node], start_node: Node):
    already_visited = set()
    for nodes in reversed(node_path[:-1]):
        # Normalize nodes into a list if it's not already
        nodes_to_check = nodes if isinstance(nodes, list) else [nodes]
        for node in nodes_to_check and node not in already_visited:
            already_visited.add(node)
    