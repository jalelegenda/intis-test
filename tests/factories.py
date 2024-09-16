from polyfactory.factories.pydantic_factory import ModelFactory

from src.entrypoint.server import User


class UserFactory(ModelFactory[User]):
    ...
