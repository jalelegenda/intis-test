# case 1:
# - apartment arrives with > 1 booking
# - bookings already exist in DB

# case: 2
# - apartment arrives with exactly one booking
# - bookings already exist in DB


# from datetime import date
# from itertools import chain
#
# from dateutil.rrule import DAILY, rrule
#
# from src.data.value import Booking
#
# ap1 = [
#     Booking(
#         id=1,
#         start_date=date(2025, 5, 10),
#         end_date=date(2025, 5, 12),
#         cleaning_deadline=date(2025, 5, 15),
#     ),
#     Booking(id=2, start_date=date(2025, 5, 15), end_date=date(2025, 5, 17)),
# ]
#
# ap2 = [
#     Booking(id=3, start_date=date(2025, 5, 10), end_date=date(2025, 5, 12)),
#     Booking(id=4, start_date=date(2025, 5, 18), end_date=date(2025, 5, 20)),
#     Booking(id=5, start_date=date(2025, 5, 10), end_date=date(2025, 5, 13)),
#     Booking(id=6, start_date=date(2025, 5, 17), end_date=date(2025, 5, 20)),
#     Booking(id=7, start_date=date(2025, 5, 10), end_date=date(2025, 5, 17)),
# ]
#
#
# cleaning_date_per_booking = list()
# for booking in ap1:
#     for d in rrule(
#         DAILY,
#         dtstart=booking.end_date,
#         until=booking.cleaning_deadline or booking.end_date,
#     ):
#         ddate = d.date()
#         cleanable_bookings_on_date = [
#             b.id
#             for b in ap2
#             if ddate >= b.end_date and ddate <= (b.cleaning_deadline or ddate)
#         ]
#         cleaning_date_per_booking.append((d, tuple(cleanable_bookings_on_date)))
#

from sqlalchemy.orm import contains_eager
from sqlmodel import select
from src.data.entity import Apartment, Booking


print(
    select(Apartment)
    .join(Booking)
    .options(contains_eager(Apartment.bookings))
    .compile()
)  # type: ignore[arg-type].where(cls.number == number and cls.user_id == user_id)
