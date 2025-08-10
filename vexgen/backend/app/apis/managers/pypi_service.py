from asyncio import TimeoutError, sleep
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientConnectorError, ClientSession


# TODO: En las nuevas actualizaciones de la API JSON se debería devolver la info de forma diferente, estar atento a nuevas versiones.
async def get_all_pypi_versions(pkg_name: str) -> list[dict[str, Any]]:
    async with ClientSession() as session:
        while True:
            try:
                async with session.get(f"https://pypi.python.org/pypi/{pkg_name}/json") as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except JSONDecodeError:
                return []
    if "releases" in response:
        versions: list[dict[str, Any]] = []
        for count, version in enumerate(response["releases"]):
            versions.append(
                {"name": version, "count": count}
            )
        return versions
    return []
