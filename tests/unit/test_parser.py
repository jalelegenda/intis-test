from io import BytesIO
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from src.web.parser import Calendar, ParserError


def test_parser_get_file_hash() -> None:
    file = BytesIO(
        b"""
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
    )
    hash_1 = Calendar.get_file_hash(file)
    file.seek(0)
    hash_2 = Calendar.get_file_hash(file)
    assert hash_1 == hash_2


def test_parser_parse(mocker: MockerFixture) -> None:
    file = BytesIO()
    get_file_hash = Mock(return_value="hash")
    get_apartment_no = Mock(return_value=1)

    mocker.patch.object(Calendar, "get_file_hash", get_file_hash)
    mocker.patch.object(Calendar, "get_apartment_no", get_apartment_no)

    parser = Calendar.parse(file, "filename", "form")
    assert parser.sha == "hash"
    assert parser.filename == "filename"
    assert parser.source == "form"
    assert parser.apartment_no == 1
    get_file_hash.assert_called_once_with(file)


def test_get_apartment_no() -> None:
    assert 1 == Calendar.get_apartment_no("apartment_1.ics")
    with pytest.raises(ParserError):
        Calendar.get_apartment_no("apartment_a.ics")
