from datetime import UTC, date, datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_core import Url
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from src.data.entity import Apartment, User
from src.data.service import ApartmentList, make_schedule_from_apartments
from src.web.auth import login_manager
from src.web.dependencies import db_manager, http_manager
from src.web.parser import Calendar

router = APIRouter()


class FileURL(BaseModel):
    url: Url


class Schedule(BaseModel):
    calendars: ApartmentList = Field(default_factory=list)
    start_date: date | None
    end_date: date | None


class CalendarsQuery(BaseModel):
    from_date: date | None = None
    to_date: date | None = None


@router.post("/import-url")
async def import_calendar_from_url(
    client: Annotated[httpx.AsyncClient, Depends(http_manager)],
    session: Annotated[AsyncSession, Depends(db_manager)],
    user: Annotated[User, Depends(login_manager)],
    payload: FileURL,
) -> JSONResponse:
    try:
        response = await client.head(url=str(payload.url))
        if "Last-Modified" in response.headers:
            last_modified = response.headers["Last-Modified"]
            apartment_no = Calendar.get_apartment_no(payload.url.path)
            apartment = await Apartment.get(session, apartment_no, user.id)
            if not apartment:
                apartment = await Apartment.create(session, apartment_no, user.id)
                response = await client.get(str(payload.url))
            if not apartment.updated_at or (
                apartment.updated_at
                < datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S GMT").replace(
                    tzinfo=UTC
                )
            ):
                calendar = Calendar.parse(response.content, str(payload.url))
                await apartment.set_schedule(session, calendar.bookings)
    except (httpx.RequestError, httpx.NetworkError, httpx.ConnectError):
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE)
    return JSONResponse(content="success", status_code=200)


@router.post("/import-calendar")
async def import_calendar(
    session: Annotated[AsyncSession, Depends(db_manager)],
    user: Annotated[User, Depends(login_manager)],
    file: UploadFile,
) -> JSONResponse:
    calendar = Calendar.parse(file.file, file.filename)  # noqa: F841
    apartment = await Apartment.get(session, calendar.apartment_no, user.id)
    if not apartment:
        apartment = await Apartment.create(session, calendar.apartment_no, user.id)
    await apartment.prepare(session)
    await apartment.set_schedule(session, calendar.bookings)
    return JSONResponse(content="File uploaded", status_code=200)


@router.get("/calendars")
async def get_calendars(
    session: Annotated[AsyncSession, Depends(db_manager)],
    user: Annotated[User, Depends(login_manager)],
    filter_query: Annotated[CalendarsQuery, Depends()],
) -> Schedule:
    apartments = await Apartment.list(
        session, user.id, filter_query.from_date, filter_query.to_date
    )
    calendars, start_date, end_date = make_schedule_from_apartments(
        apartments, filter_query.from_date, filter_query.to_date
    )
    return Schedule(calendars=calendars, start_date=start_date, end_date=end_date)


@router.get("/export/{id}")
async def export(
    session: Annotated[AsyncSession, Depends(db_manager)],
    user: Annotated[User, Depends(login_manager)],
    id: str,
) -> Response:
    apartment = await Apartment.get(session, id, user.id)
    if not apartment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    filename, content = Calendar.export(apartment)
    return Response(
        content=content,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        media_type="text/calendar",
    )
