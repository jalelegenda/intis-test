import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI

from src.web.routes import *
from src.web.dependencies import db_manager, http_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await asyncio.gather(
        db_manager.shutdown(),
        http_manager.shutdown(),
    )


app = FastAPI(lifespan=lifespan)
app.include_router(calendar_router)
app.include_router(security_router)
app.include_router(ui_router)
