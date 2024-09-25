from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from src.data.entity import User
from src.web.auth import LoginManager, login_manager
from src.web.dependencies import db_manager

router = APIRouter()


def loginmanager() -> LoginManager:
    return login_manager


@router.post("/login")
async def login(
    login: Annotated[LoginManager, Depends(loginmanager)],
    session: Annotated[AsyncSession, Depends(db_manager)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> str:
    user = await login.authenticate_user(
        session, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return login.produce_token(user.id, user.username)


@router.post("/register")
async def register(
    login: Annotated[LoginManager, Depends(loginmanager)],
    session: Annotated[AsyncSession, Depends(db_manager)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> JSONResponse:
    password_hash = login.hash_password(form_data.password)
    user = await User.create(session, form_data.username, password_hash)
    return JSONResponse(
        content={"username": user.username, "password": form_data.password}
    )
