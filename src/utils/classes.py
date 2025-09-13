from enum import Enum
from database.models import TestStatus

class FunctionInfo:
    
    def __init__(self, name: str):
        self.name = name
        
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


class TestInfo:
    def __init__(self, test_path:str, test_status:TestStatus):
        self.test_path = test_path
        self.test_status = test_status
        
    def __eq__(self, other):
        if not isinstance(other, TestInfo):
            return False
        return self.test_path == other.test_path and self.test_status == other.test_status

    def __hash__(self):
        return hash((self.test_path, self.test_status))

    def to_dict(self):
        """Convierte el objeto a un diccionario serializable"""
        return {
            "test_path": self.test_path,
            "test_status": self.test_status.value  # Usar .value para obtener el string
        }
        