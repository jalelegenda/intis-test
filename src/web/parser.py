import hashlib
from typing import BinaryIO, Literal

from ics import Calendar as iCalendar
from pydantic import BaseModel


class ParserError(Exception): ...


class Calendar(BaseModel):
    sha: str
    filename: str | None
    url: str | None = None
    source: Literal["form", "url"]
    apartment_no: int

    @classmethod
    def parse(
        cls,
        file: BinaryIO,
        filename: str | None,
        source: Literal["form", "url"],
    ):
        return cls(
            sha=cls.get_file_hash(file),
            filename=filename,
            source=source,
            apartment_no=cls.get_apartment_no(filename),
        )

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
        print(filename)
        if not filename or ("apartment" not in filename):
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
