from typing import Annotated, ClassVar

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import (
    HTTPBearer,
    OAuth2PasswordBearer,
)
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

import src.settings as settings
from src.data.entity import User
from src.web.dependencies import db_manager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class Token(BaseModel):
    sub: str
    username: str


class UserDoesNotExistError(HTTPException): ...


class TokenDecodeFailure(HTTPException): ...


class LoginManager:
    SCHEME: ClassVar = HTTPBearer()
    ALGORITHM: ClassVar = "HS256"

    def __init__(self, secret: str, token_expiration: str):
        self.secret = secret
        self.token_expiration = token_expiration

    def decode_token(self, encoded: str) -> Token:
        token_decoded = jwt.decode(encoded, self.secret, algorithms=[self.ALGORITHM])
        return Token.model_validate(token_decoded)

    def produce_token(self, user_id: str, username: str) -> str:
        token = Token(sub=user_id, username=username)
        return jwt.encode(token.model_dump(), self.secret, algorithm=self.ALGORITHM)

    async def authenticate_user(
        self,
        session: Annotated[AsyncSession, Depends(db_manager)],
        username: str,
        password: str,
    ) -> User | None:
        user = await User.get_by_username(session, username)
        if user:
            if not self.verify_password(password, user.password):
                return None
        return user

    def verify_password(self, password: str, hashed: str) -> bool:
        return pwd_context.verify(password, hashed)

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    async def __call__(
        self,
        session: Annotated[AsyncSession, Depends(db_manager)],
        token: Annotated[str, Depends(oauth2_scheme)],
    ) -> User:
        exception = {
            "status_code": status.HTTP_401_UNAUTHORIZED,
            "headers": {"WWW-Authenticate": "Bearer"},
        }
        try:
            decoded_token = self.decode_token(token)
        except jwt.InvalidTokenError:
            raise TokenDecodeFailure(detail="Cannot process token", **exception)
        user = await User.get_by_username(session, decoded_token.username)
        if not user:
            print("no user")
            raise UserDoesNotExistError(detail="User does not exist", **exception)
        return user

    async def authenticator(
        self,
        request: Request,
        session: Annotated[AsyncSession, Depends(db_manager)],
    ):
        exception = HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        token = request.cookies.get("access_token")
        if not token:
            raise exception
        scheme, _, encoded = token.partition(" ")
        if scheme != "Bearer":
            raise exception
        return await self(session, encoded)


login_manager = LoginManager(
    secret=settings.TOKEN_SECRET,
    token_expiration=settings.TOKEN_EXPIRATION,
)


def get_login_manager() -> LoginManager:
    return login_manager
