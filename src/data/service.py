from collections import defaultdict
from datetime import date, timedelta
from enum import auto
from itertools import chain
from typing import Generator, cast

from pydantic import BaseModel
from strenum import StrEnum

from src.data.entity import Apartment, Booking


class ApartmentStatus(StrEnum):
    CHECKIN = auto()
    CHECKOUT = auto()
    CLEANING = auto()
    OCCUPIED = auto()
    VACANT = auto()


class ApartmentValue(BaseModel):
    number: int
    schedule: dict[date, set[ApartmentStatus]]


class ApartmentList(BaseModel):
    apartments: list[ApartmentValue]


def make_schedule_from_apartments(
    apartments: list[Apartment],
    from_date: date | None = None,
    to_date: date | None = None,
) -> tuple[ApartmentList, date | None, date | None]:
    if not from_date:
        start_date = determine_minimal_date(get_bookings_generator(apartments))
    else:
        start_date = from_date

    if not to_date:
        end_date = determine_maximal_date(get_bookings_generator(apartments))
    else:
        end_date = to_date

    full_schedule: list[ApartmentValue] = []
    for apartment in apartments:
        apartment_schedule: defaultdict[date, set[ApartmentStatus]] = defaultdict(set)
        day = start_date
        sorted_bookings = list(sorted(apartment.bookings, key=lambda b: b.start_date))
        while sorted_bookings:
            booking = sorted_bookings.pop(0)
            print(booking)
            if day == booking.start_date:
                apartment_schedule[day].add(ApartmentStatus.CHECKIN)
                day = day + timedelta(days=1)
            else:
                while day < booking.start_date:
                    apartment_schedule[day].add(ApartmentStatus.VACANT)
                    day = day + timedelta(days=1)
                apartment_schedule[day].add(ApartmentStatus.CHECKIN)
                day = day + timedelta(days=1)

            while day < booking.end_date:
                apartment_schedule[day].add(ApartmentStatus.OCCUPIED)
                day = day + timedelta(days=1)
            apartment_schedule[day].add(ApartmentStatus.CHECKOUT)
            if day != booking.cleaning_date:
                day = day + timedelta(days=1)

            while day < cast(date, booking.cleaning_date):
                apartment_schedule[day].add(ApartmentStatus.VACANT)
                day = day + timedelta(days=1)
            apartment_schedule[day].add(ApartmentStatus.CLEANING)
            day = day + timedelta(days=1)

            forward_to = end_date

            if sorted_bookings:
                forward_to = sorted_bookings[0].start_date

            while day < forward_to:
                apartment_schedule[day].add(ApartmentStatus.VACANT)
                day = day + timedelta(days=1)

        full_schedule.append(
            ApartmentValue(number=apartment.number, schedule=dict(apartment_schedule))
        )
    return ApartmentList(apartments=full_schedule), start_date, end_date


def determine_minimal_date(bookings: Generator[Booking, None, None]) -> date:
    return min(booking.start_date for booking in bookings)


def determine_maximal_date(bookings: Generator[Booking, None, None]) -> date:
    return max((booking.cleaning_deadline or booking.end_date) for booking in bookings)


def get_bookings_generator(
    apartments: list[Apartment],
) -> Generator[Booking, None, None]:
    return (
        booking
        for booking in chain.from_iterable(
            apartment.bookings for apartment in apartments
        )
    )


def progess(day: date) -> date:
    return day + timedelta(days=1)
