from datetime import date
from enum import auto
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator
from strenum import StrEnum


class ApartmentState(StrEnum):
    OCCUPIED = auto()
    VACANT = auto()
    EXCHANGE = auto()  # briefly vacant, must be cleaned


class BaseValue(BaseModel):
    model_config = ConfigDict(frozen=True)


class Booking(BaseValue):
    start_date: date
    end_date: date
    cleaning_deadline: date | None = None
    cleaning_date: date | None = None

    @model_validator(mode="after")
    def date_consistency(self) -> Self:
        if self.start_date == self.end_date:
            raise ValueError(
                "There must be at least one day difference between start and end dates"
            )
        elif self.start_date > self.end_date:
            raise ValueError("Start date cannot come after end date")
        return self


class State(BaseValue):
    date: date
    state: ApartmentState
