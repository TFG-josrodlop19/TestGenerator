from java_analyzer.function_identifier import open_java_file, analyze_java_file
import javalang
from typing import Dict, Optional
from vexgen_caller.auth import signup, login
from dotenv import load_dotenv

load_dotenv()

if __name__== "__main__":
    login("test@example.com", "Pa$$word123")
