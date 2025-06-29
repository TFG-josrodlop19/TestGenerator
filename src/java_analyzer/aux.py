import javalang
from typing import List

def node_tree_iterator_from_leaf(node_path: List[avalang.tree.Node]):
    already_visited = set()
    for nodes in node_path:
        # Normalize nodes into a list if it's not already
        nodes_to_check = nodes if isinstance(nodes, list) else [nodes]
        for node in nodes_to_check and node not in already_visited:
            already_visited.add(node)
    