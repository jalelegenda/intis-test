from collections import defaultdict
from datetime import date
from enum import auto

from dateutil.rrule import DAILY, rrule
from pydantic import BaseModel
from strenum import StrEnum

from src.data.entity import Apartment


class ApartmentStatus(StrEnum):
    CHECKIN = auto()
    CHECKOUT = auto()
    CLEANING = auto()


class ApartmentValue(BaseModel):
    number: int
    schedule: dict[date, set[ApartmentStatus]]


def make_schedule_from_apartments(
    apartments: list[Apartment], from_date: date | None, to_date: date | None
) -> tuple[list[ApartmentValue], date | None, date | None]:
    min_date = from_date
    max_date = to_date
    full_schedule: list[ApartmentValue] = []
    for apartment in apartments:
        apartment_schedule: defaultdict[date, set[ApartmentStatus]] = defaultdict(set)
        for booking in apartment.bookings:
            if min_date is None or booking.start_date < min_date:
                min_date = booking.start_date
            if (
                max_date is None
                or (booking.cleaning_deadline or booking.end_date) > max_date
            ):
                max_date = booking.cleaning_deadline or booking.end_date

            for day in rrule(
                DAILY, dtstart=booking.start_date, until=booking.cleaning_date
            ):
                # Won't end up in calendar
                if from_date and day < from_date:
                    continue
                if to_date and day > to_date:
                    break

                if day == booking.start_date:
                    apartment_schedule[day].add(ApartmentStatus.CHECKIN)
                elif day == booking.end_date:
                    apartment_schedule[day].add(ApartmentStatus.CHECKOUT)

                if day == booking.cleaning_date:
                    apartment_schedule[day].add(ApartmentStatus.CLEANING)
                    break
        full_schedule.append(
            ApartmentValue(number=apartment.number, schedule=dict(apartment_schedule))
        )
    return full_schedule, min_date, max_date
