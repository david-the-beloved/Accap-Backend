from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    current_streak: int = Field(default=0)
    highest_streak: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReadingPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)
    goal_type: str = Field(default="daily")  # daily or weekly
    pages_per_day_goal: int = Field(default=0)
    chapters_per_day_goal: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DailyLog(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_dailylog_user_date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    date: str = Field(index=True)  # YYYY-MM-DD
    page_number: int
    chapter: str = Field(default="Unknown")
    highlighted_text: str
    goal_met: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Note(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "page_number", name="uq_note_user_page"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    page_number: int = Field(index=True)
    chapter: str = Field(default="Unknown")
    content: str = Field(default="")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserBookState(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)
    book_version: str = Field(default="default", index=True)
    baseline_page: int = Field(default=0)
    baseline_chapter: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserBookBaseline(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "book_version",
                         name="uq_user_book_baseline"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    book_version: str = Field(default="default", index=True)
    baseline_page: int = Field(default=0)
    baseline_chapter: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
