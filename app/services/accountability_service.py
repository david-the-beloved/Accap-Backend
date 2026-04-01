from datetime import datetime, timedelta

from sqlalchemy import asc, desc
from sqlmodel import Session, select

from app.models import DailyLog, ReadingPlan, User, UserBookState
from app.services.email_service import send_streak_reminder
from app.services.book_state_service import get_baseline


def _goal_met(pages_progress: int, chapter_progress: int, plan: ReadingPlan, default_value: bool) -> bool:
    checks: list[bool] = []
    if plan.pages_per_day_goal > 0:
        checks.append(pages_progress >= plan.pages_per_day_goal)
    if plan.chapters_per_day_goal > 0:
        checks.append(chapter_progress >= plan.chapters_per_day_goal)

    if not checks:
        return default_value
    return all(checks)


def evaluate_daily_accountability(session: Session) -> None:
    today_date = datetime.utcnow().date()
    today = today_date.isoformat()

    users = session.exec(select(User)).all()
    for user in users:
        if user.id is None:
            continue

        plan = session.exec(select(ReadingPlan).where(
            ReadingPlan.user_id == user.id)).first()
        if not plan:
            continue

        todays_log = session.exec(
            select(DailyLog).where(DailyLog.user_id ==
                                   user.id, DailyLog.date == today)
        ).first()

        previous_log = session.exec(
            select(DailyLog)
            .where(DailyLog.user_id == user.id, DailyLog.date < today)
            .order_by(desc(DailyLog.date))
        ).first()

        goal_met = False

        # Daily accountability: compare today's progress against the most
        # recent prior log. If none exists, fall back to a stored baseline
        # (created at book/version switch) when available.
        pages_progress = 0
        chapter_progress = 0

        # fetch any per-user book state and baseline to use if previous_log missing
        state = session.exec(
            select(UserBookState).where(UserBookState.user_id == user.id)
        ).first()
        baseline = (
            get_baseline(session, user, state.book_version if state else None)
            if state
            else None
        )

        if todays_log:
            if previous_log:
                baseline_page = previous_log.page_number
                previous_chapter = previous_log.chapter
            elif baseline:
                baseline_page = baseline.baseline_page or 0
                previous_chapter = baseline.baseline_chapter or ""
            else:
                baseline_page = 0
                previous_chapter = ""

            pages_progress = max(0, todays_log.page_number - baseline_page)
            chapter_progress = 1 if (
                (not previous_log and baseline and (
                    previous_chapter.strip().lower() != todays_log.chapter.strip().lower()))
                or (previous_log and previous_log.chapter.strip().lower() != todays_log.chapter.strip().lower())
            ) else 0

        goal_met = _goal_met(
            pages_progress=pages_progress,
            chapter_progress=chapter_progress,
            plan=plan,
            default_value=bool(todays_log),
        )
        if todays_log:
            todays_log.goal_met = goal_met

        if goal_met:
            user.current_streak += 1
            if user.current_streak > user.highest_streak:
                user.highest_streak = user.current_streak
        else:
            user.current_streak = 0
            send_streak_reminder(user.email)

    session.commit()
