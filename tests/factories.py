from polyfactory.factories.pydantic_factory import ModelFactory

from src.data.entity import Apartment, Booking
from src.data.entity import User
from src.data.value import Booking as BookingValue


class UserFactory(ModelFactory[User]): ...


class ApartmentFactory(ModelFactory[Apartment]): ...


class BookingFactory(ModelFactory[Booking]): ...


class BookingValueFactory(ModelFactory[BookingValue]): ...
