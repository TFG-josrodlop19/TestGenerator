from java_analyzer.function_identifier import open_java_file, analyze_java_file
import javalang
from typing import Dict, Optional
from vexgen_caller.auth import signup, login
from vexgen_caller.vex_generator import generate_vex, list_vex, download_vex
from dotenv import load_dotenv

load_dotenv()

if __name__== "__main__":
    # login("test@example.com", "Pa$$word123")
    # signup("test2@example.com", "Pa$$word123")
    # generate_vex("depexorg", "vex_generation", "sbom.json")
    # generate_vex("vchaindz", "sbomsign", "sbom.json")
    generate_vex("Dataport", "terminfinder-frontend", "src/sbom.json")
    # list_vex()