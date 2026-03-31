from datetime import datetime

from sqlmodel import Session, select

from app.models import DailyLog, Note, User, UserBookState, UserBookBaseline


def normalize_book_version(book_version: str | None) -> str:
    if not book_version:
        return "default"

    normalized = book_version.strip()
    return normalized or "default"


def sync_user_book_state(session: Session, user: User, book_version: str | None) -> bool:
    """Returns True when tracking data was reset because book version changed."""
    if user.id is None:
        return False

    normalized_version = normalize_book_version(book_version)

    state = session.exec(
        select(UserBookState).where(UserBookState.user_id == user.id)
    ).first()

    if not state:
        state = UserBookState(user_id=user.id, book_version=normalized_version)
        session.add(state)
        return True

    if state.book_version == normalized_version:
        return False
    # remove any existing baseline entries for this user (we'll create a new
    # baseline for the new version if the client supplies one)
    existing_baselines = session.exec(
        select(UserBookBaseline).where(UserBookBaseline.user_id == user.id)
    ).all()
    for b in existing_baselines:
        session.delete(b)

    existing_logs = session.exec(
        select(DailyLog).where(DailyLog.user_id == user.id)
    ).all()
    for log in existing_logs:
        session.delete(log)

    existing_notes = session.exec(
        select(Note).where(Note.user_id == user.id)
    ).all()
    for note in existing_notes:
        session.delete(note)

    user.current_streak = 0
    user.highest_streak = 0

    state.book_version = normalized_version
    state.updated_at = datetime.utcnow()

    return True


def create_baseline(
    session: Session,
    user: User,
    book_version: str | None,
    baseline_chapter: str | None = None,
    baseline_page: int = 0,
) -> UserBookBaseline:
    normalized_version = normalize_book_version(book_version)
    baseline_chapter_val = (baseline_chapter or "").strip() or None

    existing = session.exec(
        select(UserBookBaseline).where(
            UserBookBaseline.user_id == user.id,
            UserBookBaseline.book_version == normalized_version,
        )
    ).first()

    if existing:
        existing.baseline_page = baseline_page
        existing.baseline_chapter = baseline_chapter_val
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    record = UserBookBaseline(
        user_id=user.id,
        book_version=normalized_version,
        baseline_page=baseline_page,
        baseline_chapter=baseline_chapter_val,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_baseline(session: Session, user: User, book_version: str | None) -> UserBookBaseline | None:
    normalized_version = normalize_book_version(book_version)
    return session.exec(
        select(UserBookBaseline).where(
            UserBookBaseline.user_id == user.id,
            UserBookBaseline.book_version == normalized_version,
        )
    ).first()
