from typing import Any

from .codes.cs_code_analyzer import cs_get_used_artifacts, cs_is_imported
from .codes.java_code_analyzer import java_get_used_artifacts, java_is_imported
from .codes.js_ts_code_analyzer import js_ts_get_used_artifacts, js_ts_is_imported
from .codes.python_code_analyzer import python_get_used_artifacts, python_is_imported
from .codes.rs_code_analyzer import rs_get_used_artifacts, rs_is_imported


async def is_imported(path: str, name: str, package_manager: str) -> Any:
    match package_manager:
        case "pypi":
            if ".py" in path:
                return await python_is_imported(path, name)
        case "npm":
            if ".js" in path or ".ts" in path:
                return await js_ts_is_imported(path, name)
        case "maven":
            if ".java" in path:
                return await java_is_imported(path, name)
        case "cargo":
            if ".rs" in path:
                return await rs_is_imported
        case "nuget":
            if ".cs" in path:
                return await cs_is_imported()

async def get_used_artifacts(path: str, name: str, cve_description: str, affected_artefacts: list[str], package_manager: str) -> dict[str, list[int]]:
    match package_manager:
        case "pypi":
            return await python_get_used_artifacts(path, name, cve_description, affected_artefacts)
        case "npm":
            if "/" in name:
                name = name.split("/")[-1]
            return await js_ts_get_used_artifacts(path, name, cve_description, affected_artefacts)
        case "maven":
            name = name.split(":")[-1]
            return await java_get_used_artifacts(path, name, cve_description, affected_artefacts)
        case "cargo":
            return await rs_get_used_artifacts(path, name, cve_description, affected_artefacts)
        case "nuget":
            return await cs_get_used_artifacts(path, name, cve_description, affected_artefacts)

