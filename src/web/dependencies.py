from typing import AsyncGenerator
from httpx import AsyncClient, Timeout
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.settings import DB_STRING


class DbManager:
    def __init__(self):
        self.engine = create_async_engine(DB_STRING)
        self.session = None

    async def __call__(self) -> AsyncGenerator[AsyncSession, None]:
        if self.session is None:
            self.session = AsyncSession(self.engine)

        yield self.session
        await self.session.commit()
        await self.session.close()
        self.session = None

    async def shutdown(self) -> None:
        if self.session:
            await self.session.close_all()
        await self.engine.dispose()


class HttpManager:
    def __init__(self):
        self.client = None

    async def __call__(self) -> AsyncClient:
        if not self.client:
            self.client = AsyncClient(timeout=Timeout(60, connect=10, pool=2))

        return self.client

    async def shutdown(self) -> None:
        if self.client:
            await self.client.aclose()


db_manager = DbManager()
http_manager = HttpManager()
