import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import AsyncClient, Timeout

from src.web.dependencies import DbManager, HttpManager, DB_STRING


@pytest.fixture
def mock_engine() -> AsyncMock:
    return AsyncMock(spec=AsyncEngine)


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_async_client() -> AsyncMock:
    return AsyncMock(spec=AsyncClient)


@pytest.mark.asyncio
async def test_db_manager_initialization() -> None:
    with patch("src.web.dependencies.create_async_engine") as mock_create_engine:
        db_manager = DbManager()
        mock_create_engine.assert_called_once_with(DB_STRING)
        assert db_manager.session is None


@pytest.mark.asyncio
async def test_db_manager_call(mock_engine: AsyncMock, mock_session: AsyncMock) -> None:
    with patch("src.web.dependencies.create_async_engine", return_value=mock_engine):
        with patch("src.web.dependencies.AsyncSession", return_value=mock_session):
            db_manager = DbManager()
            async for session in db_manager():
                assert session == mock_session

            mock_session.commit.assert_awaited_once()
            mock_session.close.assert_awaited_once()
            assert db_manager.session is None


@pytest.mark.asyncio
async def test_db_manager_call_existing_session(
    mock_engine: AsyncMock, mock_session: AsyncMock
) -> None:
    with patch("src.web.dependencies.create_async_engine", return_value=mock_engine):
        db_manager = DbManager()
        db_manager.session = mock_session
        async for session in db_manager():
            assert session == mock_session

        mock_session.commit.assert_awaited_once()
        mock_session.close.assert_awaited_once()
        assert db_manager.session is None


@pytest.mark.asyncio
async def test_db_manager_shutdown(
    mock_engine: AsyncMock, mock_session: AsyncMock
) -> None:
    with patch("src.web.dependencies.create_async_engine", return_value=mock_engine):
        db_manager = DbManager()
        db_manager.session = mock_session
        await db_manager.shutdown()

        mock_session.close_all.assert_awaited_once()
        mock_engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_http_manager_initialization() -> None:
    http_manager = HttpManager()
    assert http_manager.client is None


@pytest.mark.asyncio
async def test_http_manager_call(mock_async_client: AsyncMock) -> None:
    with patch("src.web.dependencies.AsyncClient", return_value=mock_async_client):
        http_manager = HttpManager()
        client = await http_manager()
        assert client == mock_async_client
        assert http_manager.client == mock_async_client


@pytest.mark.asyncio
async def test_http_manager_call_existing_client(mock_async_client: AsyncMock) -> None:
    http_manager = HttpManager()
    http_manager.client = mock_async_client
    client = await http_manager()
    assert client == mock_async_client


@pytest.mark.asyncio
async def test_http_manager_shutdown(mock_async_client: AsyncMock) -> None:
    http_manager = HttpManager()
    http_manager.client = mock_async_client
    await http_manager.shutdown()
    mock_async_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_http_manager_client_timeout() -> None:
    with patch("src.web.dependencies.AsyncClient") as mock_async_client_class:
        http_manager = HttpManager()
        await http_manager()
        mock_async_client_class.assert_called_once_with(
            timeout=Timeout(60, connect=10, pool=2)
        )
