from pymongo import ASCENDING

from app.services.dbs.databases import get_collection, get_graph_db_driver


async def create_indexes() -> None:
    vexs_collection = get_collection("vexs")
    cves_collection = get_collection("cves")
    cpe_matchs_collection = get_collection("cpe_matchs")
    cpes_collection = get_collection("cpes")
    cpe_products_collection = get_collection("cpe_products")
    cwes_collection = get_collection("cwes")
    exploits_collection = get_collection("exploits")
    await vexs_collection.create_index([("owner", ASCENDING), ("name", ASCENDING), ("sbom_path", ASCENDING)], unique=True)
    await cves_collection.create_index("id", unique=True)
    await cpe_matchs_collection.create_index("matchCriteriaId", unique=True)
    await cpes_collection.create_index("cpeNameId", unique=True)
    await cpe_products_collection.create_index("product", unique=True)
    await cwes_collection.create_index("@ID", unique=True)
    await cwes_collection.create_index("cvelist", unique=False)
    await exploits_collection.create_index("id", unique=True)
    await exploits_collection.create_index("cvelist", unique=False)
    for driver in get_graph_db_driver("ALL"):
        async with driver.session() as session:
            await session.run(
                "create constraint if not exists for (p:Package) require p.name is unique"
            )
