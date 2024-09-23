from datetime import UTC, date, datetime
from enum import auto
from typing import NamedTuple, Self, Sequence, cast

from cuid2 import Cuid
from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, rrule
from sqlalchemy.orm import contains_eager
from sqlmodel import (
    Column,
    DateTime,
    Field,
    Index,
    Relationship,
    SQLModel,
    UniqueConstraint,
    delete,
    select,
    text,
)
from sqlmodel.ext.asyncio.session import AsyncSession
from strenum import StrEnum

from src.data.value import Booking as BookingValue

CUID = Cuid(length=32)


class DayInfo(NamedTuple):
    num_of_bookings: int
    date: date
    bookings: dict[str, "Booking"]

    def __bool__(self) -> bool:
        return len(self.bookings) > 0


class FileSource(StrEnum):
    DISK = auto()
    URL = auto()


def timezoned() -> datetime:
    return cast(
        datetime,
        Field(
            sa_column=Column(DateTime(timezone=True), nullable=False),
            default=datetime.now(UTC),
        ),
    )


class User(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=CUID.generate)
    username: str
    password: str
    created_at: datetime = timezoned()

    apartments: list["Apartment"] = Relationship(back_populates="user")


class Booking(SQLModel, table=True):
    __table_args__ = (
        Index("booking_start_date_end_date_idx", "start_date", "end_date"),
    )

    id: str = Field(primary_key=True, default_factory=CUID.generate)
    start_date: date
    end_date: date
    cleaning_deadline: date | None = None
    cleaning_date: date | None = None
    created_at: datetime = timezoned()
    updated_at: datetime = timezoned()

    apartment_id: str | None = Field(foreign_key="apartment.id", nullable=False)
    apartment: "Apartment" = Relationship(back_populates="bookings")

    async def get_overlapping_bookings(
        self, session: AsyncSession, apartment_id: str
    ) -> Sequence["Booking"]:
        # TODO: Make the commented code work to discard code after it

        # overlapping: Sequence[Booking] = (
        #     overlaps will not work for some reason
        #     will debug 10 years from now
        #     await session.exec(
        #         select(Booking)
        #         .join(Apartment)
        #         .join(User)
        #         .where(
        #             Range(
        #                 lower=new_booking.end_date,
        #                 upper=new_booking.cleaning_deadline,
        #                 bounds="[]",
        #             ).overlaps(Range(Booking.end_date, Booking.cleaning_deadline))
        #             Apartment.number != calendar.apartment_no
        #             and user.id == User.id
        #         )
        #     )
        # ).all()
        sql = select(Booking).from_statement(self.get_sql())
        results = await session.exec(  # type: ignore[no-overload]
            statement=sql,  # type: ignore[arg-type]
            params={
                "end_date": self.end_date,
                "cleaning_deadline": self.cleaning_deadline,
                "apartment_id": apartment_id,
            },
        )
        return results.scalars()

    @staticmethod
    def get_sql():
        sql = text(
            """
            SELECT * FROM booking b
            JOIN apartment a
            ON a.id = b.apartment_id
            WHERE (b.end_date , b.cleaning_deadline) OVERLAPS (:end_date, :cleaning_deadline)
                   AND a.id != :apartment_id
            """
        )
        sql = sql.columns(
            Booking.id,  # type: ignore[arg-type]
            Booking.start_date,  # type: ignore[arg-type]
            Booking.end_date,  # type: ignore[arg-type]
            Booking.cleaning_deadline,  # type: ignore[arg-type]
            Booking.cleaning_date,  # type: ignore[arg-type]
            Booking.apartment_id,  # type: ignore[arg-type]
        )
        return sql


class Apartment(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "number"),)

    id: str = Field(primary_key=True, default_factory=CUID.generate)
    number: int
    description: str | None = None
    created_at: datetime = timezoned()
    updated_at: datetime = timezoned()

    user_id: str = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="apartments")
    bookings: list[Booking] = Relationship(back_populates="apartment")

    @classmethod
    async def prepare(cls, session: AsyncSession, number: int, user_id: str) -> Self:
        apartment = (
            (
                await session.exec(
                    select(cls)
                    .join(Booking)
                    .options(contains_eager(cls.bookings))  # type: ignore[arg-type]
                    .where(cls.number == number and cls.user_id == user_id)
                )
            )
            .unique()
            .one_or_none()
        )
        if not apartment:
            apartment = cls(number=number, user_id=user_id)
            session.add(apartment)
        else:
            await apartment.delete_own_bookings(session)
            await session.refresh(apartment)
        return apartment

    async def set_schedule(
        self, session: AsyncSession, bookings: list[BookingValue]
    ) -> None:
        # TODO: Can be broken down into two functions; one iterates, other determines date for single booking
        for booking in bookings:
            new_booking = Booking(**booking.model_dump(), apartment=self)
            # TODO: need to lock the table to prevent race condition errors on import
            overlapping = tuple(
                await new_booking.get_overlapping_bookings(session, self.id)
            )
            # TODO: Optimization check on existing bookings' cleaning_dates
            # TODO: Optimization: cache dates
            best: DayInfo | None = None
            for ddate in rrule(
                DAILY,
                dtstart=new_booking.end_date,
                until=new_booking.cleaning_deadline
                or (
                    new_booking.end_date + relativedelta(months=1)
                ),  # Must be a better way to do this fallback
            ):
                day = ddate.date()
                bookings_vacant_on_ddate = {
                    b.id: b
                    for b in overlapping
                    if b.end_date <= day <= (b.cleaning_deadline or date(3000, 1, 1))
                }
                day_info = DayInfo(
                    len(bookings_vacant_on_ddate), day, bookings_vacant_on_ddate
                )
                if not best or (len(best.bookings) < len(day_info.bookings)):
                    best = day_info
            if not best:
                new_booking.cleaning_date = new_booking.end_date  # clean the room ASAP
                session.add(new_booking)
            else:
                for b in (*best.bookings.values(), new_booking):
                    b.cleaning_date = best.date
                    session.add(b)

    async def delete_own_bookings(self, session: AsyncSession) -> None:
        await session.exec(  # type: ignore[no-overload]
            delete(Booking).where(Booking.apartment_id == self.id)  # type: ignore[arg-type]
        )


class CalendarFile(SQLModel, table=True):
    url: str = Field(primary_key=True)
    source: FileSource
    sha: str

    created_at: datetime = timezoned()
    updated_at: datetime = timezoned()
