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


async def npm_create_package(
    package_name: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    all_versions = await get_all_versions(
        "npm", package_name=package_name
    )
    if all_versions:
        cpe_product = await read_cpe_product_by_package_name(package_name)
        versions = [
            await attribute_cves(version, cpe_product, "npm")
            for version in all_versions
        ]
        await create_package_and_versions(
            {"name": package_name, "moment": datetime.now()},
            versions,
            "npm",
            constraints,
            parent_id,
            parent_version_name,
        )


async def npm_search_new_versions(package: dict[str, Any]) -> None:
    no_existing_versions: dict[Any, Any] = {}
    all_versions, all_require_packages = await get_all_versions("npm", package_name=package["name"])
    counter = await count_number_of_versions_by_package(package["name"], "npm")
    if counter < len(all_versions):
        cpe_matches = await read_cpe_product_by_package_name(package["name"])
        actual_versions = await read_versions_names_by_package(package["name"], "npm")
        for version, require_packages in zip(all_versions, all_require_packages):
            if version["release"] not in actual_versions:
                version["count"] = counter
                new_version = await attribute_cves(
                    version, cpe_matches, "npm", package["name"]
                )
                no_existing_versions.update({new_version: require_packages})
                counter += 1
    await update_package_moment(package["name"], "npm")
