import asyncio
from datetime import date
from unittest.mock import Mock
from pytest_mock import MockerFixture
from typing import Any, Self, cast
import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import SelectOfScalar

from src.data.entity import Apartment, Booking
from src.data.value import Booking as BookingValue
from tests.factories import ApartmentFactory


class FakeSession:
    def __init__(self):
        self.query = None
        self.refreshed = None
        self.add_args = []

    def __call__(self, *, return_apartment: Apartment | None) -> Self:
        self.apartment = return_apartment
        return self

    def add(self, arg: Any) -> None:
        self.add_args.append(arg)

    async def exec(self, query: SelectOfScalar) -> Self:
        self.query = query
        return self

    def unique(self) -> Self:
        return self

    def one_or_none(self) -> Apartment | None:
        return self.apartment

    async def refresh(self, apartment: Apartment) -> None:
        self.refreshed = apartment


@pytest.fixture(scope="function")
def fake_session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def overlapping_bookings_1() -> list[Booking]:
    return [
        Booking(
            start_date=date(2020, 5, 1),
            end_date=date(2020, 5, 3),
            cleaning_deadline=date(2020, 5, 9),
            cleaning_date=date(2020, 5, 7),
            apartment_id="1",
        ),
        Booking(
            start_date=date(2020, 4, 29),
            end_date=date(2020, 5, 1),
            cleaning_deadline=date(2020, 5, 7),
            cleaning_date=date(2020, 5, 7),
            apartment_id="2",
        ),
        Booking(
            start_date=date(2020, 5, 2),
            end_date=date(2020, 5, 3),
            cleaning_deadline=date(2020, 5, 8),
            cleaning_date=date(2020, 5, 7),
            apartment_id="3",
        ),
        Booking(
            start_date=date(2020, 5, 4),
            end_date=date(2020, 5, 10),
            cleaning_deadline=date(2020, 5, 12),
            cleaning_date=date(2020, 5, 10),
            apartment_id="4",
        ),
        Booking(
            start_date=date(2020, 3, 1),
            end_date=date(2020, 5, 10),
            cleaning_deadline=date(2020, 5, 11),
            cleaning_date=date(2020, 5, 10),
            apartment_id="5",
        ),
        Booking(
            start_date=date(2020, 5, 1),
            end_date=date(2020, 5, 11),
            cleaning_deadline=date(2020, 5, 13),
            cleaning_date=date(2020, 5, 10),
            apartment_id="6",
        ),
    ]


@pytest.fixture
def overlapping_bookings_2() -> list[Booking]:
    return [
        Booking(
            start_date=date(2020, 6, 1),
            end_date=date(2020, 6, 3),
            cleaning_deadline=date(2020, 6, 9),
            cleaning_date=date(2020, 6, 9),
            apartment_id="1",
        ),
        Booking(
            start_date=date(2020, 6, 13),
            end_date=date(2020, 6, 15),
            cleaning_deadline=date(2020, 6, 23),
            cleaning_date=date(2020, 6, 15),
            apartment_id="2",
        ),
        Booking(
            start_date=date(2020, 6, 10),
            end_date=date(2020, 6, 12),
            cleaning_deadline=date(2020, 6, 20),
            cleaning_date=date(2020, 6, 15),
            apartment_id="3",
        ),
        Booking(
            start_date=date(2020, 6, 4),
            end_date=date(2020, 6, 5),
            cleaning_deadline=date(2020, 6, 20),
            cleaning_date=date(2020, 6, 15),
            apartment_id="4",
        ),
    ]


@pytest.mark.asyncio
async def test_prepare_apartment_when_exists(fake_session: FakeSession) -> None:
    mock = Mock()
    future: asyncio.Future[None] = asyncio.Future()
    future.set_result(None)
    mock.delete_own_bookings = Mock(return_value=future)
    result = await Apartment.prepare(
        cast(AsyncSession, fake_session(return_apartment=mock)), 10, "user_id"
    )
    assert mock == result
    mock.delete_own_bookings.assert_called_once_with(fake_session)
    assert fake_session.refreshed == mock


@pytest.mark.asyncio
async def test_prepare_apartment_when_no_apartment(
    fake_session: FakeSession, mocker: MockerFixture
) -> None:
    my_apartment = ApartmentFactory.build()
    new = Mock(return_value=my_apartment)
    mocker.patch.object(Apartment, "__new__", new)
    apartment = await Apartment.prepare(
        cast(AsyncSession, fake_session(return_apartment=None)), 10, "user_id"
    )
    new.assert_called_once_with(Apartment, number=10, user_id="user_id")
    assert my_apartment == apartment
    assert fake_session.add_args[-1] == my_apartment


@pytest.mark.asyncio
async def test_set_schedule_two_bookings_pre_existing(
    fake_session: FakeSession,
    mocker: MockerFixture,
    overlapping_bookings_1: list[Booking],
    overlapping_bookings_2: list[Booking],
) -> None:
    apartment = ApartmentFactory.build()
    mock_future_first_call = asyncio.Future()
    mock_future_first_call.set_result(overlapping_bookings_1)
    mock_future_second_call = asyncio.Future()
    mock_future_second_call.set_result(overlapping_bookings_2)
    get_overlapping_bookings = Mock(
        side_effect=[mock_future_first_call, mock_future_second_call]
    )
    mocker.patch.object(Booking, "get_overlapping_bookings", get_overlapping_bookings)
    bookings = [
        BookingValue(
            start_date=date(2020, 5, 5),
            end_date=date(2020, 5, 7),
            cleaning_deadline=date(2020, 5, 9),
        ),
        BookingValue(
            start_date=date(2020, 5, 10),
            end_date=date(2020, 6, 8),
            cleaning_deadline=date(2020, 6, 16),
        ),
    ]
    await apartment.set_schedule(
        cast(AsyncSession, fake_session),
        bookings,
    )
    assert len(fake_session.add_args) == 8
    for booking in fake_session.add_args[:4]:
        assert booking.cleaning_date == date(2020, 5, 7)
    for booking in fake_session.add_args[4:]:
        assert booking.cleaning_date == date(2020, 6, 15)


@pytest.mark.asyncio
async def test_set_schedule_single_booking_no_pre_existing(
    fake_session: FakeSession,
    mocker: MockerFixture,
) -> None:
    apartment = ApartmentFactory.build()
    mock_future_first_call = asyncio.Future()
    mock_future_first_call.set_result([])
    get_overlapping_bookings = Mock(side_effect=[mock_future_first_call])
    mocker.patch.object(Booking, "get_overlapping_bookings", get_overlapping_bookings)
    bookings = [
        BookingValue(
            start_date=date(2020, 5, 5),
            end_date=date(2020, 5, 7),
            cleaning_deadline=date(2020, 5, 9),
        ),
    ]
    await apartment.set_schedule(
        cast(AsyncSession, fake_session),
        bookings,
    )
    assert len(fake_session.add_args) == 1
    assert fake_session.add_args[-1].cleaning_date == fake_session.add_args[-1].end_date


@pytest.mark.asyncio
async def test_set_schedule_single_pre_existing_with_no_deadline(
    fake_session: FakeSession,
    mocker: MockerFixture,
) -> None:
    apartment = ApartmentFactory.build()
    mock_future_first_call = asyncio.Future()
    mock_future_first_call.set_result(
        [
            Booking(
                start_date=date(2020, 10, 10),
                end_date=date(2020, 10, 15),
                cleaning_date=date(2020, 10, 15),
                apartment_id="555",
            )
        ]
    )
    get_overlapping_bookings = Mock(side_effect=[mock_future_first_call])
    mocker.patch.object(Booking, "get_overlapping_bookings", get_overlapping_bookings)
    bookings = [
        BookingValue(
            start_date=date(2020, 10, 5),
            end_date=date(2020, 10, 16),
        ),
    ]
    await apartment.set_schedule(
        cast(AsyncSession, fake_session),
        bookings,
    )
    assert len(fake_session.add_args) == 2
    for booking in fake_session.add_args:
        assert booking.cleaning_date == date(2020, 10, 16)
