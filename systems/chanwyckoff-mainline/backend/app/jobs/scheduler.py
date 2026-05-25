from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def register_jobs() -> None:
    """Register P0 scheduler hooks.

    Real market-data jobs start in later milestones. P0 only verifies the
    scheduler lifecycle can be attached to the FastAPI app safely.
    """


def start_scheduler() -> None:
    settings = get_settings()
    if not settings.scheduler_enabled or scheduler.running:
        return
    register_jobs()
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)

