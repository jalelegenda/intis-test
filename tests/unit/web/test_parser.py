from datetime import date
from io import BytesIO
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from src.data.value import Booking
from src.web.parser import Calendar, ParserError

CALENDAR_STRING = b"""
BEGIN:VCALENDAR
VERSION:2.0
PRODID: primjer zadatka - apartment 1
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
DTSTART;VALUE=DATE:20200930
DTEND;VALUE=DATE:20201002
UID:aca171cfaa8cf1c5765e64e819906485
SUMMARY: Ivica
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20201004
DTEND;VALUE=DATE:20201010
UID:26db1820702b397cc969489412b44f6a
SUMMARY: Jurica
END:VEVENT
END:VCALENDAR
"""


def test_parser_get_file_hash() -> None:
    file = BytesIO(CALENDAR_STRING)
    hash_1 = Calendar.get_file_hash(file)
    file.seek(0)
    hash_2 = Calendar.get_file_hash(file)
    assert hash_1 == hash_2


def test_parser_parse(mocker: MockerFixture) -> None:
    file = BytesIO()
    get_file_hash = Mock(return_value="hash")
    get_apartment_no = Mock(return_value=1)
    get_icalendar = Mock(return_value=CALENDAR_STRING)
    extract_dates = Mock(return_value=[])

    mocker.patch.object(Calendar, "get_file_hash", get_file_hash)
    mocker.patch.object(Calendar, "get_apartment_no", get_apartment_no)
    mocker.patch.object(Calendar, "get_icalendar", get_icalendar)
    mocker.patch.object(Calendar, "extract_dates", extract_dates)

    parser = Calendar.parse(file, "filename", "form")
    assert parser.sha == "hash"
    assert parser.filename == "filename"
    assert parser.source == "form"
    assert parser.apartment_no == 1
    assert parser.bookings == []
    get_file_hash.assert_called_once_with(file)
    get_apartment_no.assert_called_once_with("filename")
    get_icalendar.assert_called_once_with(file)
    extract_dates.assert_called_once_with(CALENDAR_STRING)


def test_get_apartment_no() -> None:
    assert 1 == Calendar.get_apartment_no("apartment_1.ics")
    with pytest.raises(ParserError):
        Calendar.get_apartment_no("apartment_a.ics")


def test_extract_dates() -> None:
    file = BytesIO(CALENDAR_STRING)
    icalendar = Calendar.get_icalendar(file)
    assert [
        Booking(
            start_date=date(2020, 9, 30),
            end_date=date(2020, 10, 2),
            cleaning_deadline=date(2020, 10, 4),
        ),
        Booking(start_date=date(2020, 10, 4), end_date=date(2020, 10, 10)),
    ] == Calendar.extract_dates(icalendar)
