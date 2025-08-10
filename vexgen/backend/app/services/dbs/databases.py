from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config import settings


@lru_cache
def get_graph_db_driver(package_manager: str) -> AsyncDriver | tuple[AsyncDriver]:
    pypi_driver: AsyncDriver = AsyncGraphDatabase.driver(
        uri=settings.GRAPH_DB_URI_PYPI,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_PYPI),
    )
    npm_driver: AsyncDriver = AsyncGraphDatabase.driver(
        uri=settings.GRAPH_DB_URI_NPM,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_NPM),
    )
    maven_driver: AsyncDriver = AsyncGraphDatabase.driver(
        uri=settings.GRAPH_DB_URI_MAVEN,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_MAVEN),
    )
    cargo_driver: AsyncDriver = AsyncGraphDatabase.driver(
        uri=settings.GRAPH_DB_URI_CARGO,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_CARGO),
    )
    nuget_driver: AsyncDriver = AsyncGraphDatabase.driver(
        uri=settings.GRAPH_DB_URI_NUGET,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_NUGET),
    )
    match package_manager:
        case "pypi":
            return pypi_driver
        case "npm":
            return npm_driver
        case "maven":
            return maven_driver
        case "cargo":
            return cargo_driver
        case "nuget":
            return nuget_driver
        case "ALL":
            return pypi_driver, npm_driver, maven_driver, cargo_driver, nuget_driver


@lru_cache
def get_collection(collection_name: str) -> AsyncIOMotorCollection:
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.VULN_DB_URI)
    match collection_name:
        case "env_variables":
            return client.depex.get_collection(collection_name)
        case "users":
            return client.depex.get_collection(collection_name)
        case "vexs":
            return client.depex.get_collection(collection_name)
        case "cves":
            return client.nvd.get_collection(collection_name)
        case "cpe_matchs":
            return client.nvd.get_collection(collection_name)
        case "cpes":
            return client.nvd.get_collection(collection_name)
        case "cpe_products":
            return client.nvd.get_collection(collection_name)
        case "cwes":
            return client.nvd.get_collection(collection_name)
        case "exploits":
            return client.vulners_db.get_collection(collection_name)
