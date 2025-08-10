from asyncio import TimeoutError, sleep
from typing import Any

from aiohttp import ClientConnectorError, ClientSession
from xmltodict import parse


async def get_all_maven_versions(
    package_artifact_id: str, package_group_id: str
) -> list[dict[str, Any]]:
    versions: list[dict[str, Any]] = []
    async with ClientSession() as session:
        while True:
            try:
                async with session.get(f"https://repo1.maven.org/maven2/{package_group_id.replace(".", "/")}/{package_artifact_id}/maven-metadata.xml") as response:
                    xml_string = await response.text()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
    try:
        pom_dict = parse(xml_string)
    except Exception as _:
        return versions
    if isinstance(pom_dict["metadata"]["versioning"]["versions"]["version"], list):
        raw_versions = pom_dict["metadata"]["versioning"]["versions"]["version"]
    else:
        raw_versions = [pom_dict["metadata"]["versioning"]["versions"]["version"]]
    for count, version in enumerate(raw_versions):
        versions.append({"name": version, "count": count})
    return versions
