from datetime import datetime, timedelta

from fastapi import status
from fastapi.responses import JSONResponse

from app.services import read_package_by_name
from app.utils import json_encoder

from .managers.cargo_generate_controller import (
    cargo_create_package,
    cargo_search_new_versions,
)
from .managers.maven_generate_controller import (
    maven_create_package,
    maven_search_new_versions,
)
from .managers.npm_generate_controller import (
    npm_create_package,
    npm_search_new_versions,
)
from .managers.nuget_generate_controller import (
    nuget_create_package,
    nuget_search_new_versions,
)
from .managers.pypi_generate_controller import (
    pypi_create_package,
    pypi_search_new_versions,
)


async def init_pypi_package(package_name: str) -> JSONResponse:
    """
    Starts graph extraction from a Python Package Index package:

    - **package_name**: the name of the package as it appears in PyPI
    """
    package = await read_package_by_name(package_name, "pypi")
    if not package:
        await pypi_create_package(package_name)
    elif package["moment"] < datetime.now() - timedelta(days=10):
        await pypi_search_new_versions(package)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "Initializing graph"}),
    )


async def init_npm_package(package_name: str) -> JSONResponse:
    """
    Starts graph extraction from a Node Package Manager package:

    - **package_name**: the name of the package as it appears in npm
    """
    package = await read_package_by_name(package_name, "npm")
    if not package:
        await npm_create_package(package_name)
    elif package["moment"] < datetime.now() - timedelta(days=10):
        await npm_search_new_versions(package)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "initializing"}),
    )


async def init_maven_package(group_id: str, artifact_id: str) -> JSONResponse:
    """
    Starts graph extraction from a Maven Central package:

    - **group_id**: the group_id of the package as it appears in Maven Central
    - **artifact_id**: the artifact_id of the package as it appears in Maven Central
    """
    package = await read_package_by_name(artifact_id, "maven")
    if not package:
        await maven_create_package(group_id, artifact_id)
    elif package["moment"] < datetime.now() - timedelta(days=10):
        await maven_search_new_versions(package)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "initializing"}),
    )


async def init_cargo_package(package_name: str) -> JSONResponse:
    """
    Starts graph extraction from a Cargo Crates package:

    - **package_name**: the name of the package as it appears in Cargo
    """
    package = await read_package_by_name(package_name, "cargo")
    if not package:
        await cargo_create_package(package_name)
    elif package["moment"] < datetime.now() - timedelta(days=10):
        await cargo_search_new_versions(package)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "Initializing graph"}),
    )


async def init_nuget_package(package_name: str) -> JSONResponse:
    """
    Starts graph extraction from a NuGet package:

    - **package_name**: the name of the package as it appears in NuGet
    """
    package = await read_package_by_name(package_name, "nuget")
    if not package:
        await nuget_create_package(package_name)
    elif package["moment"] < datetime.now() - timedelta(days=10):
        await nuget_search_new_versions(package)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"message": "Initializing graph"}),
    )
