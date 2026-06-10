import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from config import TIMEZONE
import database as db

logger = logging.getLogger(__name__)
TZ = timezone(TIMEZONE)


async def send_broadcast(bot, broadcast_id: int):
    broadcast = await db.get_broadcast(broadcast_id)
    if not broadcast or not broadcast["is_active"]:
        return

    groups = await db.get_groups()
    if not groups:
        await db.log_send(broadcast_id, broadcast["name"], broadcast["created_by"], 0, "no_groups")
        return

    sent = 0
    for group in groups:
        try:
            await bot.send_message(group["group_id"], broadcast["text"])
            sent += 1
        except Exception as e:
            logger.warning(f"Failed to send to {group['group_id']}: {e}")

    await db.log_send(broadcast_id, broadcast["name"], broadcast["created_by"], sent)
    logger.info(f"Broadcast '{broadcast['name']}' sent to {sent}/{len(groups)} groups")


def _job_id(broadcast_id: int, hour: int) -> str:
    return f"broadcast_{broadcast_id}_h{hour}"


def schedule_broadcast(scheduler: AsyncIOScheduler, bot, broadcast: dict):
    hours = [int(h.strip()) for h in broadcast["hours"].split(",") if h.strip().isdigit()]
    for hour in hours:
        jid = _job_id(broadcast["id"], hour)
        if scheduler.get_job(jid):
            scheduler.remove_job(jid)
        scheduler.add_job(
            send_broadcast,
            trigger=CronTrigger(hour=hour, minute=0, timezone=TZ),
            args=[bot, broadcast["id"]],
            id=jid,
            replace_existing=True,
        )
        logger.info(f"Scheduled broadcast id={broadcast['id']} at {hour}:00 MSK")


def unschedule_broadcast(scheduler: AsyncIOScheduler, broadcast_id: int):
    for job in scheduler.get_jobs():
        if job.id.startswith(f"broadcast_{broadcast_id}_"):
            scheduler.remove_job(job.id)
            logger.info(f"Removed job {job.id}")


async def init_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TZ)
    broadcasts = await db.get_broadcasts()
    for bc in broadcasts:
        schedule_broadcast(scheduler, bot, bc)
    return scheduler
