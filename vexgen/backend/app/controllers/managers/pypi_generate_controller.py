from datetime import datetime
from typing import Any

from app.apis import get_all_versions
from app.controllers.cve_controller import attribute_cves
from app.services import (
    count_number_of_versions_by_package,
    create_package_and_versions,
    read_cpe_product_by_package_name,
    read_versions_names_by_package,
    update_package_moment,
)


async def pypi_create_package(
    package_name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    all_versions = await get_all_versions("pypi", package_name=package_name)
    if all_versions:
        cpe_product = await read_cpe_product_by_package_name(package_name)
        versions = [
            await attribute_cves(version, cpe_product, "pypi")
            for version in all_versions
        ]
        await create_package_and_versions(
            {"name": package_name, "moment": datetime.now()},
            versions,
            "pypi",
            constraints,
            parent_id,
            parent_version_name,
        )


async def pypi_search_new_versions(package: dict[str, Any]) -> None:
    no_existing_versions: list[dict[str, Any]] = []
    all_versions = await get_all_versions("pypi", package_name=package["name"])
    counter = await count_number_of_versions_by_package(package["name"], "pypi")
    if counter < len(all_versions):
        cpe_matches = await read_cpe_product_by_package_name(package["name"])
        actual_versions = await read_versions_names_by_package(package["name"], "pypi")
        for version in all_versions:
            if "release" in version and version["release"] not in actual_versions:
                version["count"] = counter
                new_version = await attribute_cves(
                    version, cpe_matches, "pypi", package["name"]
                )
                no_existing_versions.append(new_version)
                counter += 1
    await update_package_moment(package["name"], "pypi")
