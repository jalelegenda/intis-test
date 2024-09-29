from typing import cast
import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from src.web.auth import LoginManager, User
from tests.unit.conftest import FakeSession


@pytest.fixture
def login_manager():
    return LoginManager()


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.mark.asyncio
async def test_authenticate_user_success(
    login_manager: LoginManager, fake_session: FakeSession
):
    username = "testuser"
    password = "testpassword"
    hashed_password = login_manager.hash_password(password)
    mock_user = User(username=username, password=hashed_password)
    fake_session(return_=mock_user)

    result = await login_manager.authenticate_user(
        cast(AsyncSession, fake_session), username, password
    )

    assert result == mock_user
    assert fake_session.query is not None


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(
    login_manager: LoginManager, fake_session: FakeSession
):
    username = "testuser"
    password = "wrongpassword"
    hashed_password = login_manager.hash_password("correctpassword")
    mock_user = User(username=username, password=hashed_password)
    fake_session(return_=mock_user)

    result = await login_manager.authenticate_user(
        cast(AsyncSession, fake_session), username, password
    )

    assert result is None
    assert fake_session.query is not None


@pytest.mark.asyncio
async def test_authenticate_user_nonexistent(
    login_manager: LoginManager, fake_session: FakeSession
):
    username = "nonexistentuser"
    password = "testpassword"
    fake_session(return_=None)

    result = await login_manager.authenticate_user(
        cast(AsyncSession, fake_session), username, password
    )

    assert result is None
    assert fake_session.query is not None


@pytest.mark.asyncio
async def test_call_method_success(
    login_manager: LoginManager, fake_session: FakeSession
):
    token = login_manager.produce_token("user_id", "testuser")
    mock_user = User(username="testuser", password="p")
    fake_session(return_=mock_user)

    result = await login_manager(cast(AsyncSession, fake_session), token)

    assert result == mock_user
    assert fake_session.query is not None


@pytest.mark.asyncio
async def test_call_method_invalid_token(
    login_manager: LoginManager, fake_session: FakeSession
):
    invalid_token = "invalid_token"

    with pytest.raises(HTTPException) as exc_info:
        await login_manager(cast(AsyncSession, fake_session), invalid_token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Cannot process token"


@pytest.mark.asyncio
async def test_call_method_nonexistent_user(
    login_manager: LoginManager, fake_session: FakeSession
):
    token = login_manager.produce_token("user_id", "nonexistentuser")
    fake_session(return_=None)

    with pytest.raises(HTTPException) as exc_info:
        await login_manager(cast(AsyncSession, fake_session), token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User does not exist"
