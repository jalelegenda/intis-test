from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pytest_mock import MockerFixture

from src.data.value import ApartmentList
from src.web.auth import login_manager
from src.web.dependencies import db_manager, http_manager
from src.web.routes.api import Apartment, Calendar
from tests.factories import UserFactory
from tests.unit.conftest import FakeSession


@pytest.fixture(scope="module", autouse=True)
def login_manager_fixture(app: FastAPI):
    app.dependency_overrides[login_manager] = lambda: UserFactory.build(id="user")
    yield
    app.dependency_overrides = {}


@pytest.fixture(autouse=True)
def fake_session_override(app: FastAPI, fake_session: FakeSession):
    app.dependency_overrides[db_manager] = lambda: fake_session


@pytest.fixture(scope="function")
def mock_client(app: FastAPI):
    client = AsyncMock()
    client.head.return_value.headers = {
        "Last-Modified": "Sun, 29 Sep 2020 15:48:54 GMT"
    }
    app.dependency_overrides[http_manager] = lambda: client
    return client


@pytest.fixture(scope="function")
def parse_mock(mocker: MockerFixture) -> Mock:
    calendar = Mock()
    parse_mock = Mock(return_value=calendar)
    mocker.patch.object(Calendar, "parse", parse_mock)
    return parse_mock


@pytest.fixture(scope="function")
def mock_apartment() -> AsyncMock:
    apartment = AsyncMock()
    apartment.set_schedule.return_value = AsyncMock()
    return apartment


@pytest.mark.asyncio
async def test_import_calendar_new(
    api_client: AsyncClient,
    fake_session: FakeSession,
    mocker: MockerFixture,
    mock_client: AsyncMock,
    parse_mock: Mock,
    mock_apartment: AsyncMock,
) -> None:
    url = "http://someurl.com/apartment_10.ics"
    mock_apartment.updated_at = None
    apartment_get = AsyncMock(return_value=None)
    apartment_create = AsyncMock(return_value=mock_apartment)
    mocker.patch.object(Apartment, "get", apartment_get)
    mocker.patch.object(Apartment, "create", apartment_create)

    response = await api_client.post("/api/import-url", json={"url": url})

    assert response.status_code == 200
    mock_client.head.assert_called_once_with(url)
    mock_client.get.assert_called_once_with(url)
    apartment_get.assert_called_once_with(fake_session, 10, "user")
    apartment_create.assert_called_once_with(fake_session, 10, "user")
    parse_mock.assert_called_once_with(mock_client.get.return_value.content, url)
    mock_apartment.set_schedule.assert_called_once_with(
        fake_session, parse_mock.return_value.bookings
    )


@pytest.mark.asyncio
async def test_import_calendar_update(
    api_client: AsyncClient,
    fake_session: FakeSession,
    mocker: MockerFixture,
    mock_client: AsyncMock,
    parse_mock: Mock,
    mock_apartment: AsyncMock,
) -> None:
    url = "http://someurl.com/apartment_10.ics"
    mock_apartment.updated_at = datetime(1999, 10, 10, 20, 20, 20, tzinfo=UTC)
    apartment_get = AsyncMock(return_value=mock_apartment)
    apartment_create = AsyncMock()
    mocker.patch.object(Apartment, "get", apartment_get)
    mocker.patch.object(Apartment, "create", apartment_create)

    response = await api_client.post("/api/import-url", json={"url": url})

    assert response.status_code == 200
    mock_client.head.assert_called_once_with(url)
    mock_client.get.assert_called_once_with(url)
    apartment_get.assert_called_once_with(fake_session, 10, "user")
    apartment_create.assert_not_called()
    parse_mock.assert_called_once_with(mock_client.get.return_value.content, url)
    mock_apartment.set_schedule.assert_called_once_with(
        fake_session, parse_mock.return_value.bookings
    )


@pytest.mark.asyncio
async def test_import_calendar_up_to_date(
    api_client: AsyncClient,
    fake_session: FakeSession,
    mocker: MockerFixture,
    mock_client: AsyncMock,
    parse_mock: Mock,
    mock_apartment: AsyncMock,
) -> None:
    url = "http://someurl.com/apartment_10.ics"
    mock_apartment.updated_at = datetime(2025, 10, 10, 20, 20, 20, tzinfo=UTC)
    apartment_get = AsyncMock(return_value=mock_apartment)
    apartment_create = AsyncMock()
    mocker.patch.object(Apartment, "get", apartment_get)
    mocker.patch.object(Apartment, "create", apartment_create)

    response = await api_client.post("/api/import-url", json={"url": url})

    assert response.status_code == 200
    mock_client.head.assert_called_once_with(url)
    mock_client.get.assert_not_called()
    apartment_get.assert_called_once_with(fake_session, 10, "user")
    apartment_create.assert_not_called()
    parse_mock.assert_not_called()
    mock_apartment.set_schedule.assert_not_called()


@pytest.mark.asyncio
async def test_import_calendar_url_exceptions(
    api_client: AsyncClient,
    mock_client: AsyncMock,
) -> None:
    mock_client.head.side_effect = httpx.RequestError("fail")
    response = await api_client.post("/api/import-url", json={"url": "http://url.com"})
    assert response.status_code == 502
    mock_client.head.side_effect = httpx.NetworkError("fail")
    response = await api_client.post("/api/import-url", json={"url": "http://url.com"})
    assert response.status_code == 502
    mock_client.head.side_effect = httpx.ConnectError("fail")
    assert response.status_code == 502


@pytest.mark.asyncio
async def test_get_calendars(api_client: AsyncClient, mocker: MockerFixture) -> None:
    now = datetime.now().date()
    apartments = Mock()
    apartment_list_obj = ApartmentList(apartments=[])
    list_mock = AsyncMock(return_value=apartments)
    make_schedule_mock = Mock(return_value=tuple([apartment_list_obj, now, now]))
    mocker.patch.object(Apartment, "list", list_mock)
    mocker.patch("src.web.routes.api.make_schedule", make_schedule_mock)

    response = await api_client.get("/api/calendars")

    assert response.status_code == 200
    assert response.json() == {
        "calendars": {"apartments": []},
        "start_date": now.isoformat(),
        "end_date": now.isoformat(),
    }


@pytest.mark.asyncio
async def test_export(
    api_client: AsyncClient, mocker: MockerFixture, mock_apartment: AsyncMock
) -> None:
    apartment_get = AsyncMock(return_value=None)
    mocker.patch.object(Apartment, "get", apartment_get)
    response = await api_client.get("/api/export/10")
    assert response.status_code == 404

    apartment_get = AsyncMock(return_value=mock_apartment)
    mocker.patch.object(Apartment, "get", apartment_get)
    export_mock = Mock(return_value=tuple(["filename", b"test"]))
    mocker.patch.object(Calendar, "export", export_mock)
    response = await api_client.get("/api/export/10")
    assert response.status_code == 200
    assert response.content == b"test"
    assert "content-disposition" in response.headers
    assert response.headers["content-type"] == "text/calendar; charset=utf-8"
