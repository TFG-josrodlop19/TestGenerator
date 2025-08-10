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


async def maven_create_package(
    group_id: str,
    artifact_id: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    all_versions = await get_all_versions(
        "maven", package_artifact_id=artifact_id, package_group_id=group_id
    )
    if all_versions:
        cpe_product = await read_cpe_product_by_package_name(artifact_id)
        versions = [
            await attribute_cves(version, cpe_product, "maven")
            for version in all_versions
        ]
        await create_package_and_versions(
            {"name": artifact_id, "group_id": group_id, "moment": datetime.now()},
            versions,
            "maven",
            constraints,
            parent_id,
            parent_version_name,
        )


async def maven_search_new_versions(package: dict[str, Any]) -> None:
    no_existing_versions: list[dict[str, Any]] = []
    all_versions = await get_all_versions(
        "maven", package_artifact_id=package["name"], package_group_id=package["group_id"]
    )
    counter = await count_number_of_versions_by_package(package["name"], "maven")
    if counter < len(all_versions):
        cpe_matches = await read_cpe_product_by_package_name(package["name"])
        actual_versions = await read_versions_names_by_package(package["name"], "maven")
        for version in all_versions:
            if version["release"] not in actual_versions:
                version["count"] = counter
                new_version = await attribute_cves(
                    version, cpe_matches, "maven", package["name"]
                )
                no_existing_versions.append(new_version)
                counter += 1
    await update_package_moment(package["name"], "maven")
