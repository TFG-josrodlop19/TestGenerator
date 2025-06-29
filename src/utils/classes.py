class FunctionInfo:
    
    def __init__(self, name: str):
        self.name = name
        
        
class NodeInfo:
    
    def __init__(self, path):
        self.path = path
        
    def node(self):
        return self.path[-1] if self.path else None
    
    def qualifier(self):
        return self.node().expression.qualifier if self.node() else None