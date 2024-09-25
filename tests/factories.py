from polyfactory.factories.pydantic_factory import ModelFactory

from src.data.entity import Apartment
from src.web.app import User


class UserFactory(ModelFactory[User]): ...


class ApartmentFactory(ModelFactory[Apartment]): ...
