from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import auth, leaderboard, notes, reading_plans, reading_progress
from app.core.config import settings
from app.core.database import init_db
from app.services.scheduler import shutdown_scheduler, start_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_ready = False
    app.state.scheduler_started = False

    try:
        init_db()
        app.state.db_ready = True
        start_scheduler()
        app.state.scheduler_started = True
    except SQLAlchemyError as exc:
        logger.exception(
            "Database initialization failed during startup: %s", exc)
        logger.warning(
            "API started in degraded mode. Database-backed endpoints may fail until DB connectivity recovers."
        )

    yield

    if app.state.scheduler_started:
        shutdown_scheduler()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(reading_plans.router, prefix="/api/v1")
app.include_router(reading_progress.router, prefix="/api/v1")
app.include_router(notes.router, prefix="/api/v1")
app.include_router(leaderboard.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str | bool]:
    db_ready = bool(getattr(app.state, "db_ready", False))
    return {
        "status": "ok" if db_ready else "degraded",
        "database_ready": db_ready,
    }
