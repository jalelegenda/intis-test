from typing import Any, AsyncGenerator, Generic, Self, TypeVar

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlmodel.sql.expression import SelectOfScalar

from src.web.app import app as application
from src.web.auth import LoginManager


@pytest.fixture(scope="package")
async def app() -> FastAPI:
    return application


@pytest.fixture(scope="package")
async def api_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        app=app,
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
        self.return_ = None

    def __call__(self, *, return_: T | None) -> Self:
        self.return_ = return_
        return self

    def add(self, arg: Any = None) -> list:
        if arg is not None:
            self.add_args.append(arg)
        return self.add_args

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


@pytest.fixture(scope="session")
def token() -> str:
    return LoginManager.produce_token("id", "user")
