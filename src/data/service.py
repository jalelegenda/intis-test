from datetime import date, datetime
from itertools import chain
from typing import Generator, cast

from dateutil.rrule import DAILY, rrule

from src.data.entity import Apartment, Booking
from src.data.value import ApartmentList, ApartmentValue


def make_schedule(
    apartments: list[Apartment],
    from_date: date | None = None,
    to_date: date | None = None,
) -> tuple[ApartmentList, date | None, date | None]:
    if not apartments:
        return ApartmentList(apartments=[]), None, None
    start_date = _determine_minimal_date(_get_bookings_generator(apartments), from_date)
    end_date = _determine_maximal_date(_get_bookings_generator(apartments), to_date)

    full_schedule: list[ApartmentValue] = []
    for apartment in apartments:
        apartment_schedule = {
            dt.date(): apartment.status(dt.date())
            for dt in rrule(DAILY, dtstart=start_date, until=end_date)
        }

        full_schedule.append(
            ApartmentValue(number=apartment.number, schedule=apartment_schedule)
        )
    return ApartmentList(apartments=full_schedule), start_date, end_date


def _determine_minimal_date(
    bookings: Generator[Booking, None, None], from_date: date | None
) -> date:
    if from_date:
        return from_date
    try:
        return min(booking.start_date for booking in bookings)
    except ValueError:
        return datetime.now().date()


def _determine_maximal_date(
    bookings: Generator[Booking, None, None], to_date: date | None
) -> date:
    if to_date:
        return to_date
    try:
        return max(
            (
                booking.cleaning_deadline
                or (
                    booking.end_date
                    if booking.end_date == booking.cleaning_date
                    else cast(date, booking.cleaning_date)
                )
            )
            for booking in bookings
        )
    except ValueError:
        return datetime.now().date()


def _get_bookings_generator(
    apartments: list[Apartment],
) -> Generator[Booking, None, None]:
    return (
        booking
        for booking in chain.from_iterable(
            apartment.bookings for apartment in apartments
        )
    )
