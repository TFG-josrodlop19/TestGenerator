from .dbs.databases import get_graph_db_driver


async def read_cve_ids_by_version_and_package(
    version: str, package_name: str, package_manager: str
) -> list[str]:
    query = """
    match (p: Package) where p.name = $package_name
    match (p)-[r:Have]->(v: Version) where v.name = $version
    return v.cves
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        result = await session.run(query, version=version, package_name=package_name)
        record = await result.single()
    return record[0] if record else []


async def read_versions_names_by_package(
    package_name: str, package_manager: str
) -> list[str]:
    query = """
    match (p: Package) where p.name = $package_name
    match (p)-[r:Have]->(v: Version)
    return collect(v.name)
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        result = await session.run(query, package_name=package_name)
        record = await result.single()
    return record[0] if record else None



async def count_number_of_versions_by_package(
    package_name: str, package_manager: str
) -> int:
    query = """
    match (p: Package) where p.name = $package_name
    match (p)-[r:Have]->(v: Version)
    return count(v)
    """
    driver = get_graph_db_driver(package_manager)
    async with driver.session() as session:
        result = await session.run(query, package_name=package_name)
        record = await result.single()
    return record[0] if record else None
