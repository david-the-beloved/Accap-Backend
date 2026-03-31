from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session, select

from app.core.database import get_session
from app.models import User
from app.schemas import LeaderboardEntry

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[LeaderboardEntry])
def get_leaderboard(session: Session = Depends(get_session)) -> list[LeaderboardEntry]:
    users = session.exec(select(User).order_by(
        text("current_streak DESC"), text("highest_streak DESC"))).all()
    return [
        LeaderboardEntry(
            email=user.email,
            current_streak=user.current_streak,
            highest_streak=user.highest_streak,
        )
        for user in users
    ]
