from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.data.entity import User
from src.web.auth import login_manager

router = APIRouter()
templates = Jinja2Templates(directory="src.templates")


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request, user: Annotated[User | None, Depends(login_manager.get_user)]
) -> HTMLResponse | Response:
    if not user:
        return Response(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/loginform"},
        )
    return templates.TemplateResponse(request=request, name="index.html", context={})
