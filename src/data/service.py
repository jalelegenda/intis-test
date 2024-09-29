from datetime import date, datetime
from itertools import chain
from typing import Generator, cast

from dateutil.rrule import DAILY, rrule

from src.data.entity import Apartment, Booking
from src.data.value import ApartmentList, ApartmentValue


def make_schedule_from_apartments(
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
        # MORE PERFORMANT:
        # day = start_date
        # sorted_bookings = list(sorted(apartment.bookings, key=lambda b: b.start_date))
        # while sorted_bookings:
        #     booking = sorted_bookings.pop(0)
        #     day = _handle_start_date(booking.start_date, day, apartment_schedule)
        #     day = _handle_end_date(booking.end_date, day, apartment_schedule)
        #     day = _handle_cleaning_date(booking.cleaning_date, day, apartment_schedule)
        #     _handle_remaining_vacancy(
        #         day, apartment_schedule, end_date, sorted_bookings
        #     )

        # MORE READABLE:
        print(apartment.user_id)
        if apartment.bookings:
            print(apartment.bookings[0])
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


# def _handle_start_date(start_date: date, day: date, apartment_schedule: dict) -> date:
#     if day == start_date:
#         apartment_schedule[day].add(ApartmentStatus.CHECKIN)
#         day = progress(day)
#     elif day < start_date:
#         while day < start_date:
#             apartment_schedule[day].add(ApartmentStatus.VACANT)
#             day = progress(day)
#         apartment_schedule[day].add(ApartmentStatus.CHECKIN)
#         day = progress(day)
#     return day
#
#
# def _handle_end_date(end_date: date, day: date, apartment_schedule: dict) -> date:
#     while day < end_date:
#         apartment_schedule[day].add(ApartmentStatus.OCCUPIED)
#         day = progress(day)
#     apartment_schedule[day].add(ApartmentStatus.CHECKOUT)
#     return day
#
#
# def _handle_cleaning_date(
#     cleaning_date: date | None,
#     day: date,
#     apartment_schedule: dict,
# ) -> date:
#     if day != cleaning_date:
#         day = progress(day)
#     while day < cast(date, cleaning_date):
#         apartment_schedule[day].add(ApartmentStatus.VACANT)
#         day = progress(day)
#     apartment_schedule[day].add(ApartmentStatus.CLEANING)
#     return day
#
#
# def _handle_remaining_vacancy(
#     day: date,
#     apartment_schedule: dict,
#     end_date: date,
#     sorted_bookings: list[Booking],
# ) -> date:
#     forward_to = end_date
#
#     if sorted_bookings:
#         forward_to = sorted_bookings[0].start_date
#
#         if day == forward_to:
#             apartment_schedule[day].add(ApartmentStatus.CHECKIN)
#             day = progress(day)
#
#     day = progress(day)
#     while day < forward_to:
#         apartment_schedule[day].add(ApartmentStatus.VACANT)
#         day = progress(day)
#     return day
#
#
# def progress(day: date) -> date:
#     return day + timedelta(days=1)
