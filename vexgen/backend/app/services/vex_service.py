from typing import Any

from bson import ObjectId

from .dbs.databases import get_collection


async def create_vex(vex: dict[str, Any]) -> str:
    vexs_collection = get_collection("vexs")
    result = await vexs_collection.replace_one({"owner": vex["owner"], "name": vex["name"], "sbom_path": vex["sbom_path"]}, vex, upsert=True)
    return result.upserted_id


async def read_vex_by_id(vex_id: str) -> dict[str, Any]:
    vexs_collection = get_collection("vexs")
    return await vexs_collection.find_one({"_id": ObjectId(vex_id)})


async def read_vex_moment_by_owner_name_sbom_path(owner: str, name: str, sbom_path: str) -> dict[str, Any]:
    vexs_collection = get_collection("vexs")
    return await vexs_collection.find_one({"owner": owner, "name": name, "sbom_path": sbom_path})
