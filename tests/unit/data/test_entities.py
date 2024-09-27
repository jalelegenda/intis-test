import asyncio
from datetime import date
from typing import cast
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture
from sqlmodel.ext.asyncio.session import AsyncSession

from src.data.entity import Apartment, Booking, DayInfo
from tests.conftest import FakeSession
from tests.factories import ApartmentFactory, BookingFactory


@pytest.fixture(scope="function")
def overlapping_bookings_1() -> list[Booking]:
    return [
        Booking(
            start_date=date(2020, 5, 1),
            end_date=date(2020, 5, 3),
            cleaning_deadline=date(2020, 5, 10),
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
            end_date=date(2020, 5, 7),
            cleaning_deadline=date(2020, 5, 13),
            cleaning_date=date(2020, 5, 10),
            apartment_id="6",
        ),
    ]


@pytest.fixture(scope="function")
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
        cast(AsyncSession, fake_session(return_=mock)), 10, "user_id"
    )
    assert mock == result
    mock.delete_own_bookings.assert_called_once_with(fake_session)
    assert fake_session.refreshed == mock


@pytest.mark.asyncio
async def test_prepare_apartment_when_no_apartment(
    fake_session: FakeSession[Apartment], mocker: MockerFixture
) -> None:
    my_apartment = ApartmentFactory.build()
    new = Mock(return_value=my_apartment)
    mocker.patch.object(Apartment, "__new__", new)
    apartment = await Apartment.prepare(
        cast(AsyncSession, fake_session(return_=None)), 10, "user_id"
    )
    new.assert_called_once_with(
        Apartment, id=Apartment.make_id("user_id", 10), number=10, user_id="user_id"
    )
    assert my_apartment == apartment
    assert fake_session.add_args[-1] == my_apartment


def test_determine_best_cleaning_with_no_deadline_on_either() -> None:
    booking = Booking(
        start_date=date(2020, 5, 1),
        end_date=date(2020, 5, 3),
        apartment_id="100",
    )
    overlapping = (
        Booking(
            start_date=date(2020, 4, 29),
            end_date=date(2020, 5, 1),
            apartment_id="22",
        ),
    )
    day_info = Apartment.determine_best_cleaning_date(booking, overlapping)
    assert day_info
    assert day_info.num_of_bookings == 1
    assert day_info.date == date(2020, 5, 3)


def test_determine_best_cleaning_with_one_overlapping() -> None:
    booking = Booking(
        start_date=date(2020, 5, 1),
        end_date=date(2020, 5, 3),
        apartment_id="100",
    )
    overlapping = (
        Booking(
            start_date=date(2020, 4, 29),
            end_date=date(2020, 5, 1),
            cleaning_deadline=date(2020, 5, 4),
            apartment_id="22",
        ),
    )
    day_info = Apartment.determine_best_cleaning_date(booking, overlapping)
    assert day_info
    assert day_info.num_of_bookings == 1
    assert day_info.date == date(2020, 5, 3)


def test_determine_best_cleaning_without_overlapping() -> None:
    booking = Booking(
        start_date=date(2020, 5, 1),
        end_date=date(2020, 5, 3),
        apartment_id="100",
    )
    day_info = Apartment.determine_best_cleaning_date(booking, tuple())
    assert not day_info


def test_determine_best_cleaning_without_deadline(
    overlapping_bookings_2: list[Booking],
) -> None:
    booking = Booking(
        start_date=date(2020, 5, 1),
        end_date=date(2020, 5, 3),
        apartment_id="100",
    )
    day_info = Apartment.determine_best_cleaning_date(
        booking, tuple(overlapping_bookings_2)
    )
    assert day_info
    assert day_info.num_of_bookings == 3
    assert len(day_info.bookings) == 3
    assert day_info.date == date(2020, 6, 15)


def test_determine_best_cleaning_date(
    overlapping_bookings_1: list[Booking],
) -> None:
    booking = Booking(
        start_date=date(2020, 5, 1),
        end_date=date(2020, 5, 3),
        cleaning_deadline=date(2020, 5, 15),
        apartment_id="100",
    )
    day_info = Apartment.determine_best_cleaning_date(
        booking, tuple(overlapping_bookings_1)
    )
    assert day_info
    assert day_info.num_of_bookings == 4
    assert len(day_info.bookings) == 4
    assert day_info.date == date(2020, 5, 7)


def test_assign_cleaning_date_with_best(
    fake_session: FakeSession[Booking], overlapping_bookings_1: list[Booking]
) -> None:
    new_booking = BookingFactory.build()
    best_date = date(2020, 10, 10)
    best = DayInfo(
        8,
        best_date,
        bookings={booking.id: booking for booking in overlapping_bookings_1},
    )
    Apartment.assign_cleaning_date(cast(AsyncSession, fake_session), new_booking, best)
    for b in best.bookings.values():
        assert b.cleaning_date == best_date
        assert b in fake_session.add_args
    assert new_booking in fake_session.add_args
    assert new_booking.cleaning_date == best_date


def test_assign_cleaning_date_without_best(fake_session: FakeSession[Booking]) -> None:
    new_booking = BookingFactory.build()
    Apartment.assign_cleaning_date(cast(AsyncSession, fake_session), new_booking, None)
    assert new_booking in fake_session.add_args
    assert new_booking.cleaning_date == new_booking.end_date
