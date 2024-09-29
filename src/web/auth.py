from typing import Annotated, ClassVar

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.data.entity import User
from src.settings import settings
from src.web.dependencies import db_manager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class Token(BaseModel):
    sub: str
    username: str


class LoginManager:
    SCHEME: ClassVar = HTTPBearer()

    @staticmethod
    def decode_token(encoded: str) -> Token:
        token_decoded = jwt.decode(
            encoded, settings.token_secret, algorithms=[settings.algorithm]
        )
        return Token.model_validate(token_decoded)

    @staticmethod
    def produce_token(user_id: str, username: str) -> str:
        token = Token(sub=user_id, username=username)
        return jwt.encode(
            token.model_dump(), settings.token_secret, algorithm=settings.algorithm
        )

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

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return pwd_context.verify(password, hashed)

    @staticmethod
    def hash_password(password: str) -> str:
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
            raise HTTPException(detail="Cannot process token", **exception)
        user = await User.get_by_username(session, decoded_token.username)
        if not user:
            raise HTTPException(detail="User does not exist", **exception)
        return user

    async def authenticator(
        self,
        request: Request,
        session: Annotated[AsyncSession, Depends(db_manager)],
    ):
        exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        token = request.cookies.get("access_token")
        if not token:
            raise exception
        scheme, _, encoded = token.partition(" ")
        if scheme != "Bearer":
            raise exception
        return await self(session, encoded)


login_manager = LoginManager()


def get_login_manager() -> LoginManager:
    return login_manager
