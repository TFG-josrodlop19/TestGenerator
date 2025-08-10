from datetime import datetime
from typing import Any

from .dbs.databases import get_graph_db_driver


async def create_package_and_versions(
    package: dict[str, Any],
    versions: list[dict[str, Any]],
    package_manager: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    query_part1 = (
        """
        match (parent:RequirementFile|Version)
        where elementid(parent) = $parent_id
        """
        if parent_id
        else ""
    )
    query_part2 = f"{{name:$name,{"group_id:$group_id," if package_manager == "MVN" else ""}moment:$moment}}"
    query_part3 = (
        f"create (parent)-[rel_p:Requires{{constraints:$constraints{", parent_version_name:$parent_version_name" if parent_version_name else ""}}}]->(p)"
        if parent_id
        else ""
    )
    query = f"""
    {query_part1}
    create(p:Package{query_part2})
    {query_part3}
    with p as package
    unwind $versions as version
    create(v:Version{{
        name: version.name,
        release_date: version.release_date,
        count: version.count,
        cves: version.cves,
        mean: version.mean,
        weighted_mean: version.weighted_mean
    }})
    create (package)-[rel_v:Have]->(v)
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        result = await session.run(
            query,
            package,
            constraints=constraints,
            parent_id=parent_id,
            parent_version_name=parent_version_name,
            versions=versions,
        )
        await result.single()


async def read_package_by_name(
    package_name: str, package_manager: str
) -> dict[str, Any]:
    query = """
    match (p:Package)
    where p.name = $package_name
    return p{id: elementid(p), .*}
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        result = await session.run(query, package_name=package_name)
        record = await result.single()
    return record[0] if record else None


async def update_package_moment(package_name: str, package_manager: str) -> None:
    query = """
    match (p:Package) where p.name = $package_name
    set p.moment = $moment
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        await session.run(query, package_name=package_name, moment=datetime.now())
