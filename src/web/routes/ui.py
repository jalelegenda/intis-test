from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession

from src.data.entity import Apartment, User
from src.data.service import make_schedule
from src.web.auth import LoginManager, get_login_manager, login_manager
from src.web.dependencies import db_manager

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    user: Annotated[User, Depends(login_manager.authenticator)],
    session: Annotated[AsyncSession, Depends(db_manager)],
):
    apartments = await Apartment.list(session, user.id)
    apartments_view, min_date, max_date = make_schedule(apartments)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            **apartments_view.model_dump(),
            "start_date": min_date,
            "end_date": max_date,
        },
    )


@router.get("/signin", response_class=HTMLResponse)
async def signin(request: Request):
    return templates.TemplateResponse(request=request, name="signin.html", context={})


@router.post("/signin", response_class=RedirectResponse)
async def post_signin(
    login: Annotated[LoginManager, Depends(get_login_manager)],
    session: Annotated[AsyncSession, Depends(db_manager)],
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> RedirectResponse:
    user = await login.authenticate_user(session, form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = login.produce_token(user.id, user.username)
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response


@router.post("/register", response_class=RedirectResponse)
async def register(
    login: Annotated[LoginManager, Depends(get_login_manager)],
    session: Annotated[AsyncSession, Depends(db_manager)],
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> RedirectResponse:
    user = await User.get_by_username(session, form.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await User.create(session, form.username, login.hash_password(form.password))
    return RedirectResponse("/signin", status_code=status.HTTP_303_SEE_OTHER)
