from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


def _build_database_url() -> str:
    db_url = settings.effective_database_url

    if db_url.startswith("postgres://"):
        db_url = "postgresql+psycopg://" + db_url[len("postgres://"):]
    elif db_url.startswith("postgresql://"):
        db_url = "postgresql+psycopg://" + db_url[len("postgresql://"):]
    elif db_url.startswith("postgresql+psycopg2://"):
        db_url = "postgresql+psycopg://" + \
            db_url[len("postgresql+psycopg2://"):]

    # Supabase pooler endpoint should use 6543, not 5432.
    if "pooler.supabase.com" in db_url and ":5432/" in db_url:
        db_url = db_url.replace(":5432/", ":6543/")

    # Supabase Postgres requires SSL in production connections.
    if settings.supabase_database_url and "sslmode=" not in db_url.lower():
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}sslmode=require"

    return db_url


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
