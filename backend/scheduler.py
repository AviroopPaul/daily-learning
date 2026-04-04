import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")

IST = timezone(timedelta(hours=5, minutes=30))


async def daily_job():
    """Generate today's topic and send notifications. Runs at 9PM IST (15:30 UTC)."""
    from backend.routers.admin import run_daily_generation
    logger.info("Running daily topic generation job")
    await run_daily_generation()


def start_scheduler():
    if not scheduler.running:
        # 9PM IST = 15:30 UTC
        scheduler.add_job(
            daily_job,
            trigger=CronTrigger(hour=15, minute=30, timezone="UTC"),
            id="daily_topic",
            replace_existing=True,
            misfire_grace_time=3600,  # Allow up to 1 hour late if server was down
        )
        scheduler.start()
        logger.info("Scheduler started — daily job at 15:30 UTC (9PM IST)")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
