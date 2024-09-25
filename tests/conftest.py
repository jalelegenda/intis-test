from typing import AsyncGenerator
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
import pytest
from src.web.app import app as application


@pytest.fixture(scope="session")
async def app() -> FastAPI:
    return application


@pytest.fixture
async def api_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost",
        headers={
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiJpZCIsInVzZXJuYW1lIjoiaW50aXMifQ"
            ".v_OS-IiM7_P4Oe3Z2oROIGA1zvoIasmRbd7UebVBmMI"
        },
    ) as client:
        yield client
