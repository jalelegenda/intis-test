from typing import Annotated, ClassVar, Self

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel

from src.data.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()


class Token(BaseModel):
    SECRET: ClassVar = (
        "fd1b7507705d349a2d1644e5c4b7403cb3ce9dfecc63dd074d0cac5a8317c268"
    )
    ALGORITHM: ClassVar = "HS256"
    EXPIRATION: ClassVar = str(60 * 24 * 7)  # one week

    sub: str
    username: str

    @classmethod
    def from_encoded(cls, encoded: str) -> Self:
        token_decoded = jwt.decode(encoded, cls.SECRET, algorithms=[cls.ALGORITHM])
        return cls.model_validate(token_decoded)

    def produce(self) -> str:
        return jwt.encode(self.model_dump(), self.SECRET, algorithm=self.ALGORITHM)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


async def get_user(username: str) -> User:
    return User(id="id", username="intis", password=hash_password("password"))


async def authenticate_user(username: str, password: str) -> User | None:
    user = await get_user(username)
    if user:
        if not verify_password(password, user.password):
            return None
    return user


async def get_logged_in_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Cannot process token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        decoded_token = Token.from_encoded(token)
    except jwt.InvalidTokenError:
        raise exception
    user = await get_user(decoded_token.username)
    if not user:
        raise exception
    return user


@app.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> str:
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(sub=user.id, username=user.username).produce()


@app.get("/")
async def index(user: Annotated[User, Depends(get_logged_in_user)]) -> str:
    return "test"
