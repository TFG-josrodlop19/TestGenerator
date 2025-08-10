from typing import Any

from regex import findall, search


async def python_is_imported(file_path: str, dependency: str) -> Any:
    with open(file_path, encoding="utf-8") as file:
        try:
            code = file.read()
            return search(rf"(from|import)\s+{dependency}", code)
        except Exception as _:
            return False


async def python_get_used_artifacts(filename: str, dependency: str, cve_description: str, affected_artefacts: list[str]) -> dict[str, list[int]]:
    with open(filename, encoding="utf-8") as file:
        code = file.read()
        current_line = 1
        used_artifacts = await get_child_artifacts(dependency, code, cve_description, affected_artefacts)
        for line in code.split("\n"):
            if "import" not in line:
                for artifact in used_artifacts:
                    if artifact in line:
                        used_artifacts.setdefault(artifact, []).append(current_line)
            current_line += 1
        for artifact in list(used_artifacts.keys()):
            if not used_artifacts[artifact]:
                del used_artifacts[artifact]
        result = []
        for artifact_name, used_in_lines in used_artifacts.items():
            result.append({
                "artifact_name": artifact_name,
                "used_in_lines": used_in_lines
            })
        return result


async def get_child_artifacts(parent: str, code: str, cve_description: str, affected_artefacts: list[str]) -> dict[str, list[int]]:
    used_artifacts: dict[str, list[int]] = {}
    for _ in findall(rf"{parent}\.[^\(\)\s:]+", code):
        for artifact in _.split(".")[1:]:
            artifact_lower: str = artifact.lower()
            if artifact_lower in cve_description.lower() or artifact_lower in affected_artefacts:
                used_artifacts.setdefault(artifact.strip(), [])
    for _ in findall(rf"from\s+{parent}\.[^\(\)\s:]+\s+import\s+\w+(?:\s*,\s*\w+)*", code):
        for artifact in _.split("import")[1].split(","):
            artifact_lower: str = artifact.lower()
            if artifact_lower in cve_description.lower() or artifact_lower in affected_artefacts:
                used_artifacts.setdefault(artifact.strip(), [])
    for _ in findall(rf"from\s+{parent}\s+import\s+\w+(?:\s*,\s*\w+)*", code):
        for artifact in _.split("import")[1].split(","):
            artifact_lower: str = artifact.lower()
            if artifact_lower in cve_description.lower() or artifact_lower in affected_artefacts:
                used_artifacts.setdefault(artifact.strip(), [])
    aux = {}
    for artifact in used_artifacts:
        aux.update(await get_child_artifacts(artifact, code, cve_description, affected_artefacts))
    used_artifacts.update(aux)
    return used_artifacts
