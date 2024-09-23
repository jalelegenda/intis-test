from dataclasses import dataclass, field
import hashlib
from datetime import date
from itertools import zip_longest
from typing import BinaryIO, Literal, Self

from ics import Calendar as iCalendar

from src.data.value import Booking


class ParserError(Exception): ...


@dataclass
class Calendar:
    sha: str
    filename: str | None
    source: Literal["form", "url"]
    apartment_no: int
    url: str | None = None
    bookings: list[Booking] = field(default_factory=list)
    state: list[date] = field(default_factory=list)

    @classmethod
    def parse(
        cls,
        file: BinaryIO,
        filename: str | None,
        source: Literal["form", "url"],
    ) -> Self:
        icalendar = cls.get_icalendar(file)

        return cls(
            sha=cls.get_file_hash(file),
            filename=filename,
            source=source,
            apartment_no=cls.get_apartment_no(filename),
            bookings=cls.extract_dates(icalendar),
        )

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
                )
            )
        return bookings

    @staticmethod
    def get_file_hash(file: BinaryIO) -> str:
        blocksize = 65536  # 64kb
        buf = file.read(blocksize)
        hasher = hashlib.sha1()
        while buf:
            hasher.update(buf)
            buf = file.read(blocksize)

        return hasher.hexdigest()

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
    def get_icalendar(file: BinaryIO) -> iCalendar:
        return iCalendar(file.read().decode())
