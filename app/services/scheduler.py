from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.database import get_session_context
from app.services.accountability_service import evaluate_daily_accountability

scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)


def _run_daily_job() -> None:
    with get_session_context() as session:
        evaluate_daily_accountability(session)


def start_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        _run_daily_job,
        CronTrigger(hour=23, minute=59, timezone=settings.scheduler_timezone),
        id="daily-accountability",
        replace_existing=True,
    )
    scheduler.start()


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
