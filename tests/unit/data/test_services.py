from datetime import date

import pytest

from src.data.entity import Apartment, Booking
from src.data.service import (
    ApartmentList,
    make_schedule_from_apartments,
)
from src.data.value import ApartmentStatus


@pytest.fixture
def apartment_no_bookings():
    return Apartment(number=1, bookings=[], user_id="ja")


@pytest.fixture
def apartment_with_single_booking():
    booking = Booking(
        start_date=date(2024, 9, 1),
        end_date=date(2024, 9, 3),
        cleaning_date=date(2024, 9, 6),
        cleaning_deadline=None,
        apartment_id="aid",
    )
    return Apartment(number=2, bookings=[booking], user_id="ja")


@pytest.fixture
def apartment_with_multiple_bookings():
    booking1 = Booking(
        start_date=date(2024, 9, 2),
        end_date=date(2024, 9, 6),
        cleaning_date=date(2024, 9, 6),
        cleaning_deadline=date(2024, 9, 10),
        apartment_id="aid",
    )
    booking2 = Booking(
        start_date=date(2024, 9, 10),
        end_date=date(2024, 9, 12),
        cleaning_date=date(2024, 9, 12),
        cleaning_deadline=None,
        apartment_id="dia",
    )
    return Apartment(number=3, bookings=[booking1, booking2], user_id="on")


@pytest.fixture
def apartment_list(
    apartment_with_single_booking: Apartment,
    apartment_with_multiple_bookings: Apartment,
) -> list[Apartment]:
    return [
        apartment_with_single_booking,
        apartment_with_multiple_bookings,
    ]


def test_make_schedule_empty_apartment_list() -> None:
    result = make_schedule_from_apartments([])
    assert isinstance(result, tuple)
    assert isinstance(result[0], ApartmentList)
    assert result[0].apartments == []
    assert result[1] is None
    assert result[2] is None


def test_make_schedule_no_bookings(apartment_no_bookings) -> None:
    result = make_schedule_from_apartments([apartment_no_bookings])

    assert isinstance(result, tuple)
    assert isinstance(result[0], ApartmentList)
    assert len(result[0].apartments) == 1
    assert result[0].apartments[0].number == apartment_no_bookings.number
    assert result[0].apartments[0].schedule == {}  # No bookings, no schedule


def test_make_schedule_single_booking(apartment_with_single_booking: Apartment) -> None:
    apartments_list, start, end = make_schedule_from_apartments(
        [apartment_with_single_booking]
    )

    assert start == date(2024, 9, 1)
    assert end == date(2024, 9, 6)
    schedule = apartments_list.apartments[0].schedule
    assert schedule[date(2024, 9, 1)] == [ApartmentStatus.CHECKIN]
    assert schedule[date(2024, 9, 2)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 3)] == [ApartmentStatus.CHECKOUT]
    assert schedule[date(2024, 9, 4)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 5)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 6)] == [ApartmentStatus.CLEANING]


def test_make_schedule_multiple_bookings(
    apartment_with_multiple_bookings: Apartment,
) -> None:
    apartments_list, start, end = make_schedule_from_apartments(
        [apartment_with_multiple_bookings]
    )
    assert start == date(2024, 9, 2)
    assert end == date(2024, 9, 12)
    schedule = apartments_list.apartments[0].schedule
    assert schedule[date(2024, 9, 2)] == [ApartmentStatus.CHECKIN]
    assert schedule[date(2024, 9, 4)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 5)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 6)] == [
        ApartmentStatus.CHECKOUT,
        ApartmentStatus.CLEANING,
    ]
    assert schedule[date(2024, 9, 7)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 8)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 9)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 10)] == [ApartmentStatus.CHECKIN]
    assert schedule[date(2024, 9, 11)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 12)] == [
        ApartmentStatus.CHECKOUT,
        ApartmentStatus.CLEANING,
    ]


def test_make_schedule_bound(apartment_list: list[Apartment]) -> None:
    from_date = date(2024, 9, 1)
    to_date = date(2024, 9, 30)

    apartments_list, start, end = make_schedule_from_apartments(
        apartment_list, from_date, to_date
    )
    assert start == from_date
    assert end == to_date
    schedule = apartments_list.apartments[0].schedule
    assert schedule[date(2024, 9, 1)] == [ApartmentStatus.CHECKIN]
    assert schedule[date(2024, 9, 2)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 3)] == [ApartmentStatus.CHECKOUT]
    assert schedule[date(2024, 9, 4)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 5)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 6)] == [ApartmentStatus.CLEANING]
    assert schedule[date(2024, 9, 7)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 8)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 9)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 10)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 11)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 12)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 13)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 14)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 15)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 16)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 17)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 18)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 19)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 20)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 21)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 22)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 23)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 24)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 25)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 26)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 27)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 28)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 29)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 30)] == [ApartmentStatus.VACANT]
    schedule = apartments_list.apartments[1].schedule
    assert schedule[date(2024, 9, 1)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 2)] == [ApartmentStatus.CHECKIN]
    assert schedule[date(2024, 9, 3)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 4)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 5)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 6)] == [
        ApartmentStatus.CHECKOUT,
        ApartmentStatus.CLEANING,
    ]
    assert schedule[date(2024, 9, 7)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 8)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 9)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 10)] == [ApartmentStatus.CHECKIN]
    assert schedule[date(2024, 9, 11)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 12)] == [
        ApartmentStatus.CHECKOUT,
        ApartmentStatus.CLEANING,
    ]
    assert schedule[date(2024, 9, 13)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 14)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 15)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 16)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 17)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 18)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 19)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 20)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 21)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 22)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 23)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 24)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 25)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 26)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 27)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 28)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 29)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 30)] == [ApartmentStatus.VACANT]


def test_make_schedule_unbound(apartment_list: list[Apartment]) -> None:
    apartments_list, start, end = make_schedule_from_apartments(apartment_list)
    assert start == date(2024, 9, 1)
    assert end == date(2024, 9, 12)
    schedule = apartments_list.apartments[0].schedule
    assert schedule[date(2024, 9, 1)] == [ApartmentStatus.CHECKIN]
    assert schedule[date(2024, 9, 2)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 3)] == [ApartmentStatus.CHECKOUT]
    assert schedule[date(2024, 9, 4)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 5)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 6)] == [ApartmentStatus.CLEANING]
    assert schedule[date(2024, 9, 7)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 8)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 9)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 10)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 11)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 12)] == [ApartmentStatus.VACANT]
    schedule = apartments_list.apartments[1].schedule
    assert schedule[date(2024, 9, 1)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 2)] == [ApartmentStatus.CHECKIN]
    assert schedule[date(2024, 9, 3)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 4)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 5)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 6)] == [
        ApartmentStatus.CHECKOUT,
        ApartmentStatus.CLEANING,
    ]
    assert schedule[date(2024, 9, 7)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 8)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 9)] == [ApartmentStatus.VACANT]
    assert schedule[date(2024, 9, 10)] == [ApartmentStatus.CHECKIN]
    assert schedule[date(2024, 9, 11)] == [ApartmentStatus.OCCUPIED]
    assert schedule[date(2024, 9, 12)] == [
        ApartmentStatus.CHECKOUT,
        ApartmentStatus.CLEANING,
    ]
