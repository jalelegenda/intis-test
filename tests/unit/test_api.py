import pytest
from httpx import AsyncClient
from pytest_mock import MockerFixture

from src.web.server import Token, User
from tests.factories import UserFactory


@pytest.fixture(scope="module")
def user() -> User:
    return UserFactory().build()


@pytest.mark.asyncio
async def test_login_endpoint_success(
    api_client: AsyncClient, mocker: MockerFixture, user: User
) -> None:
    mocker.patch("src.web.server.authenticate_user", return_value=user)
    mocker.patch.object(Token, "produce", return_value="success")
    response = await api_client.post("/login", data=user.model_dump())
    assert response.status_code == 200
    assert response.json() == "success"


@pytest.mark.asyncio
async def test_login_endpoint_unauthorized(
    api_client: AsyncClient, mocker: MockerFixture
) -> None:
    mocker.patch("src.web.server.authenticate_user", return_value=None)
    response = await api_client.post(
        "/login", data={"username": "intis", "password": "password"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


@pytest.mark.asyncio
async def test_index_endpoint(api_client: AsyncClient) -> None:
    response = await api_client.get("/")
    assert response.json() == "test"
