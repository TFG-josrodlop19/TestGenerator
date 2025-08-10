from typing import Any

from bson import ObjectId

from .dbs.databases import get_collection


async def create_user(user: dict[str, str]) -> None:
    users_collection = get_collection("users")
    await users_collection.insert_one(user)


async def read_user_by_email(email: str) -> dict[str, str]:
    users_collection = get_collection("users")
    return await users_collection.find_one({"email": email})


async def read_user_vexs(user_id: str) -> list[dict[str, Any]]:
    users_collection = get_collection("users")
    pipeline: Any = [
        {
            "$match": {
                "_id": ObjectId(user_id)
            }
        },
        {
            "$lookup": {
                "from": "vexs",
                "localField": "vexs",
                "foreignField": "_id",
                "as": 'lookup'
            }
        },
        {
            "$project": {
                "_id": {"$first": "$lookup._id"},
                "owner": {"$first": "$lookup.owner"},
                "name": {"$first": "$lookup.name"},
                "sbom_path": {"$first" : "$lookup.sbom_path"}
            }
        }
    ]
    try:
        return [
            vex async for vex in users_collection.aggregate(pipeline) if vex
        ]
    except Exception as _:
        return []



async def update_user_vexs(vex_id: str, user_id: str) -> None:
    users_collection = get_collection("users")
    await users_collection.update_one({"_id": ObjectId(user_id)}, {"$addToSet": {"vexs": ObjectId(vex_id)}})


async def update_user_password(user: dict[str, Any]) -> None:
    users_collection = get_collection("users")
    return await users_collection.update_one({"email": user["email"]}, {"$set": {"password": user["password"]}})
