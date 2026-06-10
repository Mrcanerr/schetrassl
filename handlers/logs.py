from aiogram import Router, F
from aiogram.types import Message

import database as db
from utils import get_role

router = Router()


async def _can_view(user_id: int) -> bool:
    role = await get_role(user_id)
    return role in ("root", "owner")


@router.message(F.text == "📤 Отправленные рассылки")
async def sent_logs(message: Message):
    if not await _can_view(message.from_user.id):
        return await message.answer("⛔ Нет доступа.")

    logs = await db.get_send_logs(50)
    if not logs:
        return await message.answer("ℹ️ Логов отправок нет.")

    lines = []
    for log in logs:
        status_emoji = "✅" if log["status"] == "ok" else "⚠️"
        lines.append(
            f"{status_emoji} <b>{log['broadcast_name']}</b>\n"
            f"   📅 {log['sent_at'][:16]}  |  👥 групп: {log['groups_count']}\n"
            f"   👤 Создатель: <code>{log['created_by']}</code>"
        )

    # Split into chunks to avoid Telegram message length limit
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) > 3500:
            await message.answer("📤 <b>Отправленные рассылки:</b>\n\n" + chunk)
            chunk = ""
        chunk += line + "\n\n"
    if chunk:
        await message.answer("📤 <b>Отправленные рассылки:</b>\n\n" + chunk)


@router.message(F.text == "🗑 Удалённые рассылки")
async def delete_logs(message: Message):
    if not await _can_view(message.from_user.id):
        return await message.answer("⛔ Нет доступа.")

    logs = await db.get_delete_logs(50)
    if not logs:
        return await message.answer("ℹ️ Логов удалений нет.")

    lines = []
    for log in logs:
        lines.append(
            f"🗑 <b>{log['broadcast_name']}</b>\n"
            f"   📅 {log['deleted_at'][:16]}\n"
            f"   👤 Удалил: <code>{log['deleted_by']}</code>"
        )

    chunk = ""
    for line in lines:
        if len(chunk) + len(line) > 3500:
            await message.answer("🗑 <b>Удалённые рассылки:</b>\n\n" + chunk)
            chunk = ""
        chunk += line + "\n\n"
    if chunk:
        await message.answer("🗑 <b>Удалённые рассылки:</b>\n\n" + chunk)
