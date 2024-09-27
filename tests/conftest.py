from typing import Any, AsyncGenerator, Generic, Self, TypeVar

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlmodel.sql.expression import SelectOfScalar

from src import settings
from src.web.app import app as application
from src.web.auth import LoginManager


@pytest.fixture(scope="session")
async def app() -> FastAPI:
    return application


@pytest.fixture(scope="session")
def token() -> str:
    return LoginManager(settings.TOKEN_SECRET, settings.TOKEN_EXPIRATION).produce_token(
        "id", "user"
    )


@pytest.fixture
async def api_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost",
    ) as client:
        yield client
        app.dependency_overrides = {}


T = TypeVar("T")


class FakeSession(Generic[T]):
    def __init__(self):
        self.query = None
        self.refreshed = None
        self.add_args = []

    def __call__(self, *, return_: T | None) -> Self:
        self.return_ = return_
        return self

    def add(self, arg: Any) -> None:
        self.add_args.append(arg)

    async def exec(self, query: SelectOfScalar) -> Self:
        self.query = query
        return self

    def unique(self) -> Self:
        return self

    def one_or_none(self) -> T | None:
        return self.return_

    async def refresh(self, refreshed: T) -> None:
        self.refreshed = refreshed


@pytest.fixture(scope="function")
def fake_session() -> FakeSession:
    return FakeSession()
