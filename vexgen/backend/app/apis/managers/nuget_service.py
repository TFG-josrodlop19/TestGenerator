from asyncio import TimeoutError, sleep
from typing import Any

from aiohttp import ClientConnectorError, ClientSession


async def get_all_nuget_versions(pkg_name: str) -> list[dict[str, Any]]:
    async with ClientSession() as session:
        while True:
            try:
                async with session.get(f"https://api.nuget.org/v3/registration5-gz-semver2/{pkg_name}/index.json") as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
    if "items" in response:
        versions: list[dict[str, Any]] = []
        for count, version in response["items"]["items"]:
            versions.append(
                {"name": version["catalogEntry"]["version"], "count": count}
            )
        return versions
    return []
