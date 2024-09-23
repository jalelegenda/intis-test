from datetime import date

import pytest

from src.data.value import Booking


def test_booking_validation() -> None:
    some_date = date(2020, 10, 10)
    with pytest.raises(ValueError):
        Booking(start_date=some_date, end_date=date(2019, 10, 10))
    with pytest.raises(ValueError):
        Booking(start_date=some_date, end_date=some_date)
