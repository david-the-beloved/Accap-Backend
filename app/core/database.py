from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


def _build_database_url() -> str:
    return settings.effective_database_url


engine = create_engine(
    _build_database_url(),
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_timeout=30,
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
