from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


def _build_database_url() -> str:
    return settings.effective_database_url


def _build_connect_args() -> dict:
    # Supabase pooler (pgbouncer) can break with server-side prepared statements.
    # Disabling auto-preparation avoids DuplicatePreparedStatement errors.
    if settings.uses_supabase_pooler:
        return {"prepare_threshold": None}
    return {}


engine = create_engine(
    _build_database_url(),
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_timeout=30,
    connect_args=_build_connect_args(),
)


@contextmanager
def get_session_context():
    with Session(engine) as session:
        yield session


def get_session():
    with Session(engine) as session:
        yield session


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
