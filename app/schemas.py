from datetime import datetime
from typing import Literal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class GoogleSignInRequest(BaseModel):
    id_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    current_streak: int
    highest_streak: int


class ReadingPlanUpsert(BaseModel):
    goal_type: Literal["daily"] = "daily"
    pages_per_day_goal: int = Field(default=0, ge=0)
    chapters_per_day_goal: int = Field(default=0, ge=0)


class ReadingPlanResponse(BaseModel):
    id: int
    user_id: int
    goal_type: str
    pages_per_day_goal: int
    chapters_per_day_goal: int
    updated_at: datetime


class ProgressUpdateRequest(BaseModel):
    page_number: int = Field(ge=1)
    chapter: str = Field(min_length=1)
    highlighted_text: str = Field(min_length=1)
    book_version: Optional[str] = None
    baseline_chapter: Optional[str] = None
    date: Optional[str] = None


class DailyLogResponse(BaseModel):
    id: int
    user_id: int
    date: str
    page_number: int
    chapter: str
    highlighted_text: str
    goal_met: bool


class NoteUpsertRequest(BaseModel):
    page_number: int = Field(ge=1)
    chapter: str = "Unknown"
    content: str
    book_version: Optional[str] = None


class NoteResponse(BaseModel):
    id: int
    user_id: int
    page_number: int
    chapter: str
    content: str


class LeaderboardEntry(BaseModel):
    email: EmailStr
    current_streak: int
    highest_streak: int
