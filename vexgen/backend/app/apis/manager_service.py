from typing import Any

from .managers.cargo_service import get_all_cargo_versions
from .managers.maven_service import get_all_maven_versions
from .managers.npm_service import get_all_npm_versions
from .managers.pypi_service import get_all_pypi_versions


async def get_all_versions(
    manager: str,
    package_name: str | None = None,
    package_artifact_id: str | None = None,
    package_group_id: str | None = None,
) -> list[dict[str, Any]]:
    match manager:
        case "pypi":
            return await get_all_pypi_versions(package_name)
        case "npm":
            return await get_all_npm_versions(package_name)
        case "maven":
            return await get_all_maven_versions(package_artifact_id, package_group_id)
        case "cargo":
            return await get_all_cargo_versions(package_name)
        case "nuget":
            return await get_all_npm_versions(package_name)
