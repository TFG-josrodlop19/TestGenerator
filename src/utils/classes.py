from javalang.tree import MethodInvocation

class FunctionInfo:
    
    def __init__(self, name: str):
        self.name = name
        
        
class NodeInfo:
    
    def __init__(self, path, node):
        self.path = path
        self.node = node

    def qualifier(self):
        print(self.node)
        qualifier = None
        if isinstance(self.node, MethodInvocation):
            qualifier = self.node.qualifier
        else:
            qualifier = self.node.expression.qualifier
        return qualifier
    
class ArtifactInfoVex:
    def __init__(self, file_path:str, target_line:int, target_name:str):
        self.file_path = file_path
        self.target_line = target_line
        self.target_name = target_name
        
    def __eq__(self, other):
        if not isinstance(other, ArtifactInfoVex):
            return False
        return (self.file_path == other.file_path and 
                self.target_line == other.target_line and 
                self.target_name == other.target_name)

    def __hash__(self):
        return hash((self.file_path, self.target_line, self.target_name))
    
    def __str__(self):
        return f"ArtifactInfoVex(file_path='{self.file_path}', target_line={self.target_line}, target_name='{self.target_name}')"