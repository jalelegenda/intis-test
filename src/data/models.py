from datetime import date, datetime

from cuid2 import Cuid
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint, create_engine

CUID = Cuid(length=32)


class User(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=CUID.generate)
    username: str
    password: str

    apartments: list["Apartment"] = Relationship(back_populates="user")


class ApartmentCleaningDateLink(SQLModel, table=True):
    apartment_id: str | None = Field(
        default=None, foreign_key="apartment.id", primary_key=True
    )
    cleaning_date_id: str | None = Field(
        default=None, foreign_key="cleaningdate.id", primary_key=True
    )


class Apartment(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "number"),
        UniqueConstraint("user_id", "name", postgresql_nulls_not_distinct=True),
    )

    id: str | None = Field(primary_key=True, default_factory=CUID.generate)
    number: int
    name: str | None

    user_id: str = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="apartments")
    bookings: list["Booking"] = Relationship(back_populates="apartment")
    cleaning_dates: list["CleaningDate"] = Relationship(back_populates="apartments", link_model=ApartmentCleaningDateLink)


class CleaningDate(SQLModel, table=True):
    id: str | None = Field(primary_key=True, default_factory=CUID.generate)
    date: date

    apartments: list[Apartment] = Relationship(back_populates="cleaning_dates", link_model=ApartmentCleaningDateLink)


class Booking(SQLModel, table=True):
    id: str | None = Field(primary_key=True, default_factory=CUID.generate)
    start_date: datetime
    end_date: datetime

    apartment_id: str = Field(foreign_key="apartment.id")
    apartment: Apartment = Relationship(back_populates="bookings")
