from typing import AsyncGenerator
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
import pytest
from src.web.server import app as server


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return server


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


