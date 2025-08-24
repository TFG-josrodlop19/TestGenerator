from typing import Dict, Optional
from vexgen_caller.auth import signup, login
from vexgen_caller.vex_generator import generate_vex, open_vex_file
from dotenv import load_dotenv

load_dotenv()

if __name__== "__main__":
    # login("test@example.com", "Pa$$word123")
    # signup("test2@example.com", "Pa$$word123")
    # generate_vex("depexorg", "vex_generation", "sbom.json")
    # generate_vex("vchaindz", "sbomsign", "sbom.json")
    # generate_vex("Dataport", "terminfinder-frontend", "src/sbom.json")
    generate_vex("TFG-josrodlop19", "TestGenerator", "vulnerableCodeExamples/jacksonDatabind-CWE-502/sbom.json")
    # open_vex_file("depexorg", "vex_generation")