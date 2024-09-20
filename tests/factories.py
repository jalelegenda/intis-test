from polyfactory.factories.pydantic_factory import ModelFactory

from src.web.server import User


class UserFactory(ModelFactory[User]):
    ...
