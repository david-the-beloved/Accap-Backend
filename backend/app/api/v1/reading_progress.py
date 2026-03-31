from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies import get_current_user
from app.models import DailyLog, ReadingPlan, User
from app.schemas import DailyLogResponse, ProgressUpdateRequest
from app.services.book_state_service import (
    sync_user_book_state,
    create_baseline,
)

router = APIRouter(prefix="/reading-progress", tags=["reading-progress"])


@router.post("/update", response_model=DailyLogResponse)
def update_progress(
    payload: ProgressUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DailyLogResponse:
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    plan = session.exec(
        select(ReadingPlan).where(ReadingPlan.user_id == current_user.id)
    ).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set your daily reading goal before starting.",
        )

    changed = sync_user_book_state(session, current_user, payload.book_version)

    # If we just created or switched the user's book state and the client
    # provided a baseline chapter, store a dedicated baseline record so that
    # accountability calculations can compare against a real baseline without
    # polluting DailyLog history.
    if changed and getattr(payload, "baseline_chapter", None):
        create_baseline(
            session,
            current_user,
            payload.book_version,
            baseline_chapter=payload.baseline_chapter,
            baseline_page=0,
        )

    today = payload.date or datetime.utcnow().date().isoformat()
    normalized_chapter = payload.chapter.strip() or "Unknown"
    normalized_highlight = payload.highlighted_text.strip()

    row = session.exec(
        select(DailyLog).where(DailyLog.user_id ==
                               current_user.id, DailyLog.date == today)
    ).first()

    if not row:
        row = DailyLog(
            user_id=current_user.id,
            date=today,
            page_number=payload.page_number,
            chapter=normalized_chapter,
            highlighted_text=normalized_highlight,
        )
        session.add(row)
    else:
        row.page_number = payload.page_number
        row.chapter = normalized_chapter
        row.highlighted_text = normalized_highlight
        row.updated_at = datetime.utcnow()

    session.commit()
    session.refresh(row)

    return DailyLogResponse(**row.model_dump())


@router.get("/latest", response_model=DailyLogResponse | None)
def get_latest_progress(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    book_version: str | None = Query(None, alias="book_version"),
) -> DailyLogResponse | None:
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    # If the client provides the current book_version, ensure the server
    # syncs state and clears existing progress/notes when the version changed.
    if book_version is not None:
        changed = sync_user_book_state(session, current_user, book_version)
        if changed:
            session.commit()
            return None

    latest = session.exec(
        select(DailyLog)
        .where(DailyLog.user_id == current_user.id)
        .order_by(DailyLog.updated_at.desc(), DailyLog.id.desc())
    ).first()

    if not latest:
        return None

    return DailyLogResponse(**latest.model_dump())
