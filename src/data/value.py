from datetime import date
from enum import auto
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator
from strenum import StrEnum


class BaseValue(BaseModel):
    model_config = ConfigDict(frozen=True)


class Booking(BaseValue):
    start_date: date
    end_date: date
    cleaning_deadline: date | None = None
    cleaning_date: date | None = None
    summary: str | None = None

    @model_validator(mode="after")
    def date_consistency(self) -> Self:
        if self.start_date == self.end_date:
            raise ValueError(
                "There must be at least one day difference between start and end dates"
            )
        elif self.start_date > self.end_date:
            raise ValueError("Start date cannot come after end date")
        return self


class ApartmentStatus(StrEnum):
    CHECKIN = auto()
    CHECKOUT = auto()
    CLEANING = auto()
    OCCUPIED = auto()
    VACANT = auto()


class ApartmentValue(BaseModel):
    number: int
    schedule: dict[date, list[ApartmentStatus]]


class ApartmentList(BaseModel):
    apartments: list[ApartmentValue]
