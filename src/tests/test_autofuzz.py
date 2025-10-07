import pytest
from autofuzz.autofuzz import generate_fuzz_tests, build_tests, execute_tests
from database.models import ConfidenceLevel
from database.operations import find_last_scanner_confidence, get_created_fuzzers_by_project, get_last_scanner_data_by_project
from pathlib import Path
import os

owner = "TFG-josrodlop19"
name = "VulnerableProject4"
pom_path = "pom.xml"
confidence = ConfidenceLevel.LOW

def test_generate_fuzz_tests():
    generate_fuzz_tests(owner, name, pom_path, confidence)
    
    project_root = Path(__file__).parent.parent.parent
    test_file_path = project_root / "OSS-Fuzz" / "projects" / "tfg-josrodlop19_vulnerableproject4" / "src" / "test" / "java" / "VulnerableAppLoadFuzzer.java"
    
    assert test_file_path.exists(), f"Test file not found at: {test_file_path}"
    assert test_file_path.stat().st_size > 0, f"Test file is empty: {test_file_path}"
    
    with open(test_file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    
    # Comprobar que contiene el texto específico
    expected_text = "This fuzzer class is a generic template generated in case of error."
    assert expected_text in file_content, f"Expected text not found in file."
    assert find_last_scanner_confidence(owner, name) == confidence
    
    test_file_path = project_root / "OSS-Fuzz" / "projects" / "tfg-josrodlop19_vulnerableproject4" / "src" / "test" / "java" / "VulnerableAppMainFuzzer.java"
    
    assert test_file_path.exists(), f"Test file not found at: {test_file_path}"
    assert test_file_path.stat().st_size > 0, f"Test file is empty: {test_file_path}"
    
    with open(test_file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    
    # Comprobar que contiene el texto específico
    expected_text = "VulnerableApp.main(args);"
    assert expected_text in file_content, f"Expected text not found in file."
    
    

def test_build_tests():
    build_tests(owner, name)
    fuzzers = get_created_fuzzers_by_project(owner, name)
    assert len(fuzzers) == 2, "No created fuzzers found for the project"""
    
    for fuzzer in fuzzers:
        assert fuzzer.name in ["VulnerableAppMainFuzzer", "VulnerableAppProcessyamlFuzzer"], f"Unexpected fuzzer name: {fuzzer.name}"


def test_execute_tests():
    execute_tests(owner, name, ConfidenceLevel.LOW)
    results = get_last_scanner_data_by_project(owner, name)
    tests = set()
    for vulnerability in results.vulnerabilities:
        for artifact in vulnerability.artifacts:
            for test in artifact.tests:
                tests.add(test)
                assert test.status in ["VULNERABLE", "NOT_VULNERABLE"], f"Unexpected test status for test {test.name}: expected one of ['VULNERABLE', 'NOT_VULNERABLE'] but got {test.status}"
        