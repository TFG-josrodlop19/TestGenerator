from java_analyzer.function_identifier import open_java_file, analyze_java_file
import javalang
from typing import Dict, Optional


if __name__== "__main__":
    # data = analyze_java_file("vulnerableCodeExamples/VulnerableCodeCall.java", 10, "processInput")
    # data = analyze_java_file("vulnerableCodeExamples/VulnerableCodeCall.java", 10, "processInput")
    # data = analyze_java_file("vulnerableCodeExamples/VulnerableCode.java", 29, "triggerVulnerability")
    # data = analyze_java_file("vulnerableCodeExamples/VulnerableCode2.java", 16, "leerLinea")
    data = analyze_java_file("vulnerableCodeExamples/VulnerableCode4.java", 5, "length")
    print(data)