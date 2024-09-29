from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from src.web.routes.login import get_login_manager


@pytest.mark.asyncio
async def test_login_endpoint_success(
    app: FastAPI,
    api_client: AsyncClient,
) -> None:
    login_mock = Mock()
    login_mock.authenticate_user = AsyncMock()
    login_mock.produce_token.return_value = "token"
    app.dependency_overrides[get_login_manager] = lambda: login_mock
    response = await api_client.post(
        url="/api/login",
        data={"username": "intis", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.json() == "token"
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_endpoint_unauthorized(
    app: FastAPI,
    api_client: AsyncClient,
) -> None:
    login_mock = Mock()
    login_mock.authenticate_user = AsyncMock(return_value=None)
    app.dependency_overrides[get_login_manager] = lambda: login_mock
    response = await api_client.post(
        "/api/login",
        data={"username": "intis", "password": "password"},
    )
    assert response.json() == {"detail": "Incorrect username or password"}
    assert response.status_code == 401
