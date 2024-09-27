import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse

from src.web.dependencies import db_manager, http_manager
from src.web.routes import *


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await asyncio.gather(
        db_manager.shutdown(),
        http_manager.shutdown(),
    )


app = FastAPI(lifespan=lifespan)


@app.exception_handler(HTTPException)
async def unauthenticated_redirect(request: Request, exc: HTTPException):
    if (
        exc.status_code == status.HTTP_401_UNAUTHORIZED
        and "/api" not in request.url.path
    ):
        return RedirectResponse(url="/signin")
    if exc.status_code == status.HTTP_409_CONFLICT:
        return RedirectResponse(url="/signin")
    return JSONResponse(
        content={"detail": exc.detail}, headers=exc.headers, status_code=exc.status_code
    )


api_router = APIRouter(prefix="/api")
api_router.include_router(calendar_router)
api_router.include_router(login_router)

app.include_router(ui_router)
app.include_router(api_router)
