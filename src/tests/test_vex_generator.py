import pytest
import os

import requests
from database.models import VulnerabilityStatus
from vexgen_caller.vex_generator import generate_vex, generate_download_path, get_tix_data

def test_generate_vex():
    generate_vex("TFG-josrodlop19", "VulnerableProject1")
    path = generate_download_path("TFG-josrodlop19", "VulnerableProject1")
    assert os.path.exists(path)


def test_get_tix_data():
    vulnerabilities, artifacts = get_tix_data("TFG-josrodlop19", "VulnerableProject1")
    assert isinstance(vulnerabilities, list)
    assert len(vulnerabilities) > 0
    assert len(artifacts) > 0
    
    vulnerability = vulnerabilities[0]
    
    assert vulnerability.artifacts is not None
    assert len(vulnerability.artifacts) > 0
    artifacts_list = list(vulnerability.artifacts)
    assert artifacts_list[0].filePath.endswith("JsonProcessor.java")
    
    
    assert artifacts.__contains__("file_path")
    assert artifacts.__contains__("target_line")
    assert artifacts.__contains__("target_name")
    
def test_generate_vex_repository_not_exists(capsys):
    with pytest.raises(requests.HTTPError):
        generate_vex("ExampleOwner", "NonExistentRepo")
        
    
def test_get_tix_data_no_file():
    with pytest.raises(FileNotFoundError):
        get_tix_data("ExampleOwner", "NonExistentRepo")