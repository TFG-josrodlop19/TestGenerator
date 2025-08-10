from contextlib import asynccontextmanager
from typing import Any

from bson.errors import InvalidId
from fastapi import FastAPI, Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, Response

from app.router import api_router
from app.services import create_indexes

DESCRIPTION = """
A backend for dependency graph building, atribution of vulnerabilities and reasoning
over it.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    await create_indexes()
    yield


app = FastAPI(
    title="Depex",
    description=DESCRIPTION,
    # openapi_url=None,
    version="0.6.2",
    contact={
        "name": "Antonio Germán Márquez Trujillo",
        "url": "https://github.com/GermanMT",
        "email": "amtrujillo@us.es",
    },
    license_info={
        "name": "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(
    request: Request, exc: HTTPException
) -> Response:
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> Response:
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(InvalidId)
async def object_id_exception_handler(
    request: Request, exc: InvalidId
) -> Response:
    return JSONResponse(
        status_code=400,
        content={"message": "The Object Id is invalid"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:3000'
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
