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