from polyfactory.factories.pydantic_factory import ModelFactory

from src.data.entity import Apartment, Booking
from src.data.entity import User


class UserFactory(ModelFactory[User]): ...


class ApartmentFactory(ModelFactory[Apartment]): ...


class BookingFactory(ModelFactory[Booking]): ...
