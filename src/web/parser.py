from dataclasses import dataclass, field
from datetime import date
from itertools import zip_longest
from tempfile import SpooledTemporaryFile
from typing import BinaryIO, Self

from ics import Calendar as iCalendar
from ics import Event
from ics.event import Arrow

from src.data.entity import Apartment
from src.data.value import Booking


class ParserError(Exception): ...


@dataclass
class Calendar:
    filename: str | None
    apartment_no: int
    url: str | None = None
    bookings: list[Booking] = field(default_factory=list)
    state: list[date] = field(default_factory=list)

    @classmethod
    def parse(
        cls,
        file: bytes | SpooledTemporaryFile | BinaryIO,
        filename: str | None,
    ) -> Self:
        if isinstance(file, SpooledTemporaryFile):
            file = bytes(file.read())
        elif isinstance(file, BinaryIO):
            file = file.read()
        icalendar = cls.get_icalendar(file)

        return cls(
            filename=filename,
            apartment_no=cls.get_apartment_no(filename),
            bookings=cls.extract_dates(icalendar),
        )

    @staticmethod
    def export(
        apartment: Apartment,
    ) -> tuple[str, bytes]:
        calendar = iCalendar()
        for booking in apartment.bookings:
            event = Event()
            event.description = booking.guest_name
            event.begin = Arrow.fromdate(booking.start_date)
            event.end = Arrow.fromdate(booking.end_date)
            calendar.events.add(event)
        return f"apartment_{apartment.number}.ics", calendar.serialize().encode()

    @staticmethod
    def extract_dates(icalendar: iCalendar) -> list[Booking]:
        bookings = []
        events_sorted = sorted(list(icalendar.events), key=lambda e: e.begin)
        for event, next_event in zip_longest(events_sorted, events_sorted[1:]):
            bookings.append(
                Booking(
                    start_date=event.begin.date(),
                    end_date=event.end.date(),
                    cleaning_deadline=next_event.begin.date() if next_event else None,
                    summary=event.description and str(event.description),
                )
            )
        return bookings

    @staticmethod
    def get_apartment_no(filename: str | None) -> int:
        error = ParserError("Cannot parse apartment number")
        if not filename:
            raise error

        try:
            filename_no_ext, *_ = filename.rpartition(".")
            *_, apartment_no = filename_no_ext.rpartition("_")
            return int(apartment_no)
        except ValueError as e:
            raise error from e

    @staticmethod
    def get_icalendar(file: bytes) -> iCalendar:
        return iCalendar(file.decode())
