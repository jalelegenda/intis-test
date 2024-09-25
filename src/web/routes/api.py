from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, UploadFile
from fastapi.responses import JSONResponse
from httpx import AsyncClient
from pydantic import BaseModel, Field
from pydantic_core import Url
from sqlmodel.ext.asyncio.session import AsyncSession

from src.data.entity import Apartment, User
from src.data.service import ApartmentValue, make_schedule_from_apartments
from src.web.auth import login_manager
from src.web.dependencies import db_manager, http_manager
from src.web.parser import Calendar

router = APIRouter()


class FileURL(BaseModel):
    url: Url


class Schedule(BaseModel):
    calendars: list[ApartmentValue] = Field(default_factory=list)
    start_date: date | None
    end_date: date | None


class CalendarsQuery(BaseModel):
    from_date: date | None = None
    to_date: date | None = None


@router.post("/import-url")
async def import_calendar_from_url(
    client: Annotated[AsyncClient, Depends(http_manager)],
    session: Annotated[AsyncSession, Depends(db_manager)],
    user: Annotated[User, Depends(login_manager)],
    payload: FileURL,
) -> JSONResponse:
    response = await client.head(url=str(payload.url))
    if "Last-Modified" in response.headers:
        last_modified = response.headers["Last-Modified"]
        apartment_no = Calendar.get_apartment_no(payload.url.path)
        apartment = await Apartment.prepare(session, apartment_no, user.id)
        if apartment.updated_at < datetime.fromisoformat(last_modified):
            response = await client.get(str(payload.url))
            calendar = Calendar.parse(response.content, str(payload.url))
            await apartment.set_schedule(session, calendar.bookings)
    return JSONResponse(content="success", status_code=200)


@router.post("/import-calendar")
async def import_calendar(
    session: Annotated[AsyncSession, Depends(db_manager)],
    user: Annotated[User, Depends(login_manager)],
    file: UploadFile,
) -> JSONResponse:
    calendar = Calendar.parse(file.file, file.filename)  # noqa: F841
    apartment = await Apartment.prepare(session, calendar.apartment_no, user.id)
    await apartment.set_schedule(session, calendar.bookings)
    return JSONResponse(content="File uploaded", status_code=200)


@router.get("/calendars")
async def get_calendars(
    session: Annotated[AsyncSession, Depends(db_manager)],
    user: Annotated[User, Depends(login_manager)],
    filter: Annotated[CalendarsQuery, Query()],
) -> Schedule:
    apartments = await Apartment.list(
        session, user.id, filter.from_date, filter.to_date
    )
    calendars, start_date, end_date = make_schedule_from_apartments(
        apartments, filter.from_date, filter.to_date
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
        raise FileNotFoundError
    filename, content = Calendar.export(apartment)
    return Response(
        content=content,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        media_type="text/calendar",
    )
