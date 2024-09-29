from datetime import UTC, date, datetime
from itertools import dropwhile, takewhile
from typing import Generator, NamedTuple, Self, Sequence, Union, cast

from cuid2 import Cuid
from dateutil.rrule import DAILY, rrule
from sqlalchemy.orm import contains_eager
from sqlmodel import (
    Column,
    DateTime,
    Field,
    Index,
    Relationship,
    SQLModel,
    delete,
    select,
)
from sqlmodel.ext.asyncio.session import AsyncSession

from src.data.value import ApartmentStatus
from src.data.value import Booking as BookingValue

CUID = Cuid(length=32)


class DayInfo(NamedTuple):
    num_of_bookings: int
    date: date
    bookings: dict[str, "Booking"]

    def __bool__(self) -> bool:
        return len(self.bookings) > 0


def timezoned(nullable: bool = False) -> datetime:
    return cast(
        datetime,
        Field(
            sa_column=Column(DateTime(timezone=True), nullable=nullable),
            default=datetime.now(UTC),
        ),
    )


class User(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=CUID.generate)
    username: str
    password: str
    created_at: datetime = timezoned()

    apartments: list["Apartment"] = Relationship(back_populates="user")

    @classmethod
    async def create(cls, session: AsyncSession, username: str, password: str) -> Self:
        user = cls(username=username, password=password)
        session.add(user)
        return user

    @staticmethod
    async def get_by_username(
        session: AsyncSession, username: str
    ) -> Union["User", None]:
        return (
            await session.exec(select(User).where(User.username == username))
        ).one_or_none()


class Booking(SQLModel, table=True):
    __table_args__ = (
        Index("booking_start_date_end_date_idx", "start_date", "end_date"),
    )

    id: str = Field(primary_key=True, default_factory=CUID.generate)
    start_date: date
    end_date: date
    cleaning_deadline: date | None = Field(default=None, nullable=False)
    cleaning_date: date | None = Field(default=None, nullable=False)
    guest_name: str | None = None
    created_at: datetime = timezoned()
    updated_at: datetime = timezoned()

    apartment_id: str | None = Field(foreign_key="apartment.id", nullable=False)
    apartment: "Apartment" = Relationship(back_populates="bookings")

    async def get_overlapping_bookings(
        self, session: AsyncSession, apartment_id: str
    ) -> Sequence["Booking"]:
        return (
            (
                await session.exec(
                    select(Booking)
                    .join(Apartment)
                    .where(self.start_date <= Booking.end_date)
                    .where(self.end_date > Booking.start_date)
                    .where(Apartment.id != apartment_id)
                    .with_for_update()
                )
            )
            .unique()
            .all()
        )


class Apartment(SQLModel, table=True):
    id: str | None = Field(primary_key=True, default=None)
    number: int
    created_at: datetime = timezoned()
    updated_at: datetime | None = timezoned(nullable=True)

    user_id: str = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="apartments")
    bookings: list[Booking] = Relationship(back_populates="apartment")

    @staticmethod
    def make_id(user_id: str, number: int | str) -> str:
        return f"{user_id}.{number}"

    @classmethod
    async def get(
        cls, session: AsyncSession, number: int | str, user_id: str
    ) -> Self | None:
        apartment = await session.exec(
            select(cls)
            .join(Booking)
            .options(contains_eager(cls.bookings))  # type: ignore[arg-type]
            .where(cls.id == cls.make_id(user_id, number))
            .order_by(Booking.start_date)  # type: ignore[arg-type]
        )
        return apartment.unique().one_or_none()

    @classmethod
    async def create(
        cls, session: AsyncSession, number: int | str, user_id: str
    ) -> Self:
        apartment = cls(
            id=cls.make_id(user_id, number),
            number=int(number),
            user_id=user_id,
            updated_at=None,
        )
        session.add(apartment)
        return apartment

    def status(self, dt: date) -> list[ApartmentStatus]:
        overlapping_bookings = list(
            takewhile(
                lambda b: b.start_date <= dt <= b.cleaning_date,  # type: ignore[operator]
                dropwhile(
                    lambda b: (b.start_date > dt or b.cleaning_date < dt),
                    self.bookings,  # type: ignore[operator]
                ),
            )
        )
        # a maximum of two bookings can overlap and
        # if they do it means a checkin, a checkout and a cleaning
        # is must happen that day
        if not overlapping_bookings:
            return [ApartmentStatus.VACANT]

        if len(overlapping_bookings) == 2:
            if (
                overlapping_bookings[0].end_date
                == overlapping_bookings[0].cleaning_date
            ):
                return [
                    ApartmentStatus.CHECKOUT,
                    ApartmentStatus.CLEANING,
                    ApartmentStatus.CHECKIN,
                ]
            return [
                ApartmentStatus.CLEANING,
                ApartmentStatus.CHECKIN,
            ]

        if (
            overlapping_bookings[0].end_date == dt
            and overlapping_bookings[0].cleaning_date == dt
        ):
            return [ApartmentStatus.CHECKOUT, ApartmentStatus.CLEANING]
        if overlapping_bookings[0].start_date == dt:
            return [ApartmentStatus.CHECKIN]
        if overlapping_bookings[0].end_date == dt:
            return [ApartmentStatus.CHECKOUT]
        if overlapping_bookings[0].cleaning_date == dt:
            return [ApartmentStatus.CLEANING]
        if overlapping_bookings[0].start_date < dt < overlapping_bookings[0].end_date:
            return [ApartmentStatus.OCCUPIED]
        else:
            return [ApartmentStatus.VACANT]

    async def prepare(
        self,
        session: AsyncSession,
    ) -> Self:
        await self.delete_own_bookings(session)
        await session.refresh(self)
        return self

    async def set_schedule(
        self, session: AsyncSession, bookings: list[BookingValue]
    ) -> None:
        for booking in bookings:
            new_booking = Booking(**booking.model_dump(), apartment=self)
            overlapping = tuple(
                await new_booking.get_overlapping_bookings(session, cast(str, self.id))
            )
            best = self.determine_best_cleaning_date(new_booking, overlapping)
            self.assign_cleaning_date(session, new_booking, best)
        self.updated_at = datetime.now(tz=UTC)

    def determine_best_cleaning_date(
        self, booking: Booking, overlapping: tuple[Booking, ...]
    ) -> DayInfo | None:
        best: DayInfo | None = None
        if not overlapping:
            return best
        deadline = self.get_furthest_deadline(overlapping)
        end_date = self.get_furthest_end_date_generator(overlapping, booking)
        for ddate in rrule(
            DAILY,
            dtstart=booking.end_date,
            until=(
                booking.cleaning_deadline
                or deadline
                or max(end_date)  # fallback to latest checkout
            ),
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

        return best

    @staticmethod
    def get_furthest_deadline(overlapping: tuple[Booking, ...]) -> date | None:
        deadlines: list[date] = [
            o.cleaning_deadline for o in overlapping if o.cleaning_deadline is not None
        ]
        furthest_deadline = None
        if deadlines:
            furthest_deadline = max(deadlines)
        return furthest_deadline

    @staticmethod
    def get_furthest_end_date_generator(
        overlapping: tuple[Booking, ...],
        booking: Booking,
    ) -> Generator[date, None, None]:
        return (
            o.end_date
            for o in (
                *overlapping,
                booking,
            )  # leave this to minimize performance hit
        )

    @staticmethod
    def assign_cleaning_date(
        session: AsyncSession, booking: Booking, best: DayInfo | None
    ) -> None:
        if not best:
            booking.cleaning_date = booking.end_date  # clean the room ASAP
            session.add(booking)
        else:
            for b in (*best.bookings.values(), booking):
                b.cleaning_date = best.date
                session.add(b)

    @staticmethod
    async def list(
        session: AsyncSession,
        user_id: str,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list["Apartment"]:
        statement = (
            select(Apartment).join(Booking).options(contains_eager(Apartment.bookings))  # type: ignore[arg-type]
        )

        if from_date:
            statement = statement.where(Booking.end_date >= from_date)
        if to_date:
            statement = statement.where(Booking.start_date < to_date)

        statement = statement.where(Apartment.user_id == user_id).order_by(
            Booking.start_date  # type: ignore[arg-type]
        )

        result = await session.exec(statement)
        return list(result.unique().all())

    async def delete_own_bookings(self, session: AsyncSession) -> None:
        await session.exec(  # type: ignore[call-overload]
            delete(Booking).where(Booking.apartment_id == self.id)  # type: ignore[arg-type]
        )
