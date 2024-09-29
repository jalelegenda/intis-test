from datetime import UTC, date, datetime
from typing import cast
from unittest.mock import AsyncMock, Mock, call

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture
from sqlmodel.ext.asyncio.session import AsyncSession

from src.data.entity import Apartment, Booking, DayInfo, User
from src.data.value import ApartmentStatus
from tests.unit.conftest import FakeSession
from tests.factories import (
    ApartmentFactory,
    BookingFactory,
    BookingValueFactory,
    UserFactory,
)


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
async def test_create_user(fake_session: FakeSession, mocker: MockerFixture) -> None:
    mock_user = UserFactory.build()
    mock_new = Mock(return_value=mock_user)
    mocker.patch.object(User, "__new__", mock_new)
    user = await User.create(fake_session, mock_user.username, mock_user.password)  # type: ignore[arg-type]
    assert user == mock_user
    assert fake_session.add() == [mock_user]
    mock_new.assert_called_once_with(
        User, username=mock_user.username, password=mock_user.password
    )


def test_make_id() -> None:
    assert "user.10" == Apartment.make_id("user", 10)


@pytest.mark.asyncio
async def test_create_apartment(
    fake_session: FakeSession, mocker: MockerFixture
) -> None:
    mock_apartment = ApartmentFactory.build()
    mock_new = Mock(return_value=mock_apartment)
    mock_make_id = Mock(return_value="id")
    mocker.patch.object(Apartment, "__new__", mock_new)
    mocker.patch.object(Apartment, "make_id", mock_make_id)
    apartment = await Apartment.create(
        fake_session,  # type: ignore[arg-type]
        mock_apartment.number,
        mock_apartment.user_id,
    )
    assert apartment == mock_apartment
    assert fake_session.add() == [mock_apartment]
    mock_new.assert_called_once_with(
        Apartment,
        id="id",
        number=mock_apartment.number,
        user_id=mock_apartment.user_id,
        updated_at=None,
    )
    mock_make_id.assert_called_once_with(mock_apartment.user_id, mock_apartment.number)


@pytest.mark.asyncio
async def test_prepare(fake_session: FakeSession, mocker: MockerFixture) -> None:
    mock_delete_own_bookings = AsyncMock()
    mocker.patch.object(Apartment, "delete_own_bookings", mock_delete_own_bookings)
    apartment = ApartmentFactory.build()
    await apartment.prepare(cast(AsyncSession, fake_session))
    assert fake_session.refreshed == apartment
    mock_delete_own_bookings.assert_called_once_with(fake_session)


@pytest.mark.asyncio
async def test_set_schedule(
    fake_session: FakeSession,
    overlapping_bookings_2: list[Booking],
    mocker: MockerFixture,
) -> None:
    now = datetime.now()
    apartment = ApartmentFactory.build(id="user")
    booking_values = [
        BookingValueFactory.build(
            start_date=date(2020, 5, 5),
            end_date=date(2020, 6, 6),
            summary="1",
        ),
        BookingValueFactory.build(
            start_date=date(2020, 7, 7),
            end_date=date(2020, 8, 8),
            summary="2",
        ),
    ]
    day_info = DayInfo(0, now, {})

    booking_instance_mock = AsyncMock()
    booking_instance_mock.get_overlapping_bookings.return_value = tuple(
        overlapping_bookings_2
    )
    booking_mock = Mock(spec=Booking, return_value=booking_instance_mock)
    determine_best_cleaning_date_mock = Mock(return_value=day_info)
    assign_cleaning_date_mock = Mock()
    mocker.patch.object(
        Apartment, "determine_best_cleaning_date", determine_best_cleaning_date_mock
    )
    mocker.patch.object(Apartment, "assign_cleaning_date", assign_cleaning_date_mock)
    mocker.patch("src.data.entity.Booking", booking_mock)

    with freeze_time(now):
        await apartment.set_schedule(fake_session, booking_values)  # type: ignore[arg-type]

        assert apartment.updated_at == now.replace(tzinfo=UTC)
        assert len(booking_values) == booking_mock.call_count
        booking_mock.assert_has_calls(
            [
                call(**booking_values[0].model_dump(), apartment=apartment),
                call(**booking_values[1].model_dump(), apartment=apartment),
            ]
        )
        booking_instance_mock.get_overlapping_bookings.assert_called_with(
            fake_session,
            cast(str, apartment.id),
        )
        assert (
            len(booking_values)
            == booking_instance_mock.get_overlapping_bookings.call_count
        )
        determine_best_cleaning_date_mock.assert_called_with(
            booking_instance_mock, tuple(overlapping_bookings_2)
        )
        assert len(booking_values) == determine_best_cleaning_date_mock.call_count
        assign_cleaning_date_mock.assert_called_with(
            fake_session, booking_instance_mock, day_info
        )
        assert len(booking_values) == assign_cleaning_date_mock.call_count


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
    apartment = ApartmentFactory.build(bookings=[booking])
    day_info = apartment.determine_best_cleaning_date(booking, overlapping)
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
    apartment = ApartmentFactory.build(bookings=[booking])
    day_info = apartment.determine_best_cleaning_date(booking, overlapping)
    assert day_info
    assert day_info.num_of_bookings == 1
    assert day_info.date == date(2020, 5, 3)


def test_determine_best_cleaning_without_overlapping() -> None:
    booking = Booking(
        start_date=date(2020, 5, 1),
        end_date=date(2020, 5, 3),
        apartment_id="100",
    )
    apartment = ApartmentFactory.build(bookings=[booking])
    day_info = apartment.determine_best_cleaning_date(booking, tuple())
    assert not day_info


def test_determine_best_cleaning_without_deadline(
    overlapping_bookings_2: list[Booking],
) -> None:
    booking = Booking(
        start_date=date(2020, 5, 1),
        end_date=date(2020, 5, 3),
        apartment_id="100",
    )
    apartment = ApartmentFactory.build(bookings=[booking])
    day_info = apartment.determine_best_cleaning_date(
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
    apartment = ApartmentFactory.build(bookings=[booking])
    day_info = apartment.determine_best_cleaning_date(
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
        assert b in fake_session.add()
    assert new_booking in fake_session.add()
    assert new_booking.cleaning_date == best_date


def test_assign_cleaning_date_without_best(fake_session: FakeSession[Booking]) -> None:
    new_booking = BookingFactory.build()
    Apartment.assign_cleaning_date(cast(AsyncSession, fake_session), new_booking, None)
    assert new_booking in fake_session.add()
    assert new_booking.cleaning_date == new_booking.end_date


def test_apartment_status(bookings: list[Booking]) -> None:
    apartment = ApartmentFactory.build()

    apartment.bookings = bookings
    assert [ApartmentStatus.VACANT] == apartment.status(date(2020, 6, 9))
    assert [ApartmentStatus.CHECKIN] == apartment.status(date(2020, 6, 10))
    assert [ApartmentStatus.OCCUPIED] == apartment.status(date(2020, 6, 11))
    assert [
        ApartmentStatus.CHECKOUT,
        ApartmentStatus.CLEANING,
        ApartmentStatus.CHECKIN,
    ] == apartment.status(date(2020, 6, 12))
    assert [ApartmentStatus.CHECKOUT, ApartmentStatus.CLEANING] == apartment.status(
        date(2020, 6, 14)
    )
    assert [ApartmentStatus.VACANT] == apartment.status(date(2020, 6, 19))
    assert [ApartmentStatus.CLEANING, ApartmentStatus.CHECKIN] == apartment.status(
        date(2020, 6, 28)
    )
    assert [ApartmentStatus.VACANT] == apartment.status(date(2020, 7, 21))

    apartment.bookings = []
    assert [ApartmentStatus.VACANT] == apartment.status(date(2020, 7, 21))
