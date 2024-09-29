from datetime import date

import pytest

from src.data.entity import Booking


@pytest.fixture(scope="function")
def bookings() -> list[Booking]:
    return [
        Booking(
            start_date=date(2020, 6, 10),
            end_date=date(2020, 6, 12),
            cleaning_deadline=date(2020, 6, 12),
            cleaning_date=date(2020, 6, 12),
            apartment_id="user.4",
        ),
        Booking(
            start_date=date(2020, 6, 12),
            end_date=date(2020, 6, 14),
            cleaning_deadline=date(2020, 6, 20),
            cleaning_date=date(2020, 6, 14),
            apartment_id="user.4",
        ),
        Booking(
            start_date=date(2020, 6, 20),
            end_date=date(2020, 6, 25),
            cleaning_deadline=date(2020, 6, 28),
            cleaning_date=date(2020, 6, 28),
            apartment_id="user.4",
        ),
        Booking(
            start_date=date(2020, 6, 28),
            end_date=date(2020, 7, 5),
            cleaning_deadline=date(2020, 7, 15),
            cleaning_date=date(2020, 7, 10),
            apartment_id="user.4",
        ),
    ]
