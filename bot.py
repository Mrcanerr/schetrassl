import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from scheduler import init_scheduler
from handlers import (
    common,
    admin,
    broadcast_create,
    broadcast_list,
    logs,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    scheduler = await init_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Pass scheduler + bot via workflow_data so handlers can access them
    dp["scheduler"] = scheduler
    dp["broadcast_bot"] = bot

    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(broadcast_create.router)
    dp.include_router(broadcast_list.router)
    dp.include_router(logs.router)

    try:
        logger.info("Bot started")
        await dp.start_polling(bot, scheduler=scheduler, broadcast_bot=bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
