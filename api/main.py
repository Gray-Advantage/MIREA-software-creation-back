from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import engine
from api.routers import (
    adjustments,
    auth,
    company,
    easter_eggs,
    employees,
    health,
    me,
    qr,
    schedule,
    statistics,
    time_entries,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await engine.dispose()


app = FastAPI(
    title="StaffTracker API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(company.router, prefix="/api/company", tags=["Company"])
app.include_router(
    employees.router,
    prefix="/api/employees",
    tags=["Employees"],
)
app.include_router(
    adjustments.router,
    prefix="/api/employees",
    tags=["Adjustments"],
)
app.include_router(me.router, prefix="/api/me", tags=["Me"])
app.include_router(qr.router, prefix="/api/qr", tags=["QR"])
app.include_router(
    time_entries.router,
    prefix="/api/time-entries",
    tags=["TimeEntries"],
)
app.include_router(
    schedule.router,
    prefix="/api/schedule",
    tags=["Schedule"],
)
app.include_router(
    statistics.router,
    prefix="/api/statistics",
    tags=["Statistics"],
)
app.include_router(easter_eggs.router)
