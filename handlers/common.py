from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

import database as db
from config import ROOT_ID
from keyboards import main_menu, admin_panel_kb, logs_menu_kb
from utils import get_role

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    role = await get_role(message.from_user.id)
    is_root = role == "root"
    is_owner = role in ("root", "owner")
    await message.answer(
        "👋 Привет! Я бот рассылок.\nВыберите действие:",
        reply_markup=main_menu(is_root=is_root, is_owner=is_owner),
    )


@router.message(Command("info"))
@router.message(F.text == "ℹ️ Info")
async def cmd_info(message: Message):
    chat = message.chat
    user = message.from_user

    if chat.type in ("group", "supergroup"):
        group_id = chat.id
        group_title = chat.title or "—"
        in_whitelist = await db.is_group_whitelisted(group_id)

        # Find which owners are members — we just show all owners
        all_owners = await db.get_owners()
        owners_text = (
            "\n".join(
                f"  • {o['username'] or '—'} (ID: {o['user_id']})" for o in all_owners
            )
            if all_owners
            else "  нет овнеров"
        )

        await message.answer(
            f"<b>ℹ️ Информация о группе</b>\n\n"
            f"📌 Название: <b>{group_title}</b>\n"
            f"🆔 ID группы: <code>{group_id}</code>\n"
            f"✅ В белом списке: <b>{'Да' if in_whitelist else 'Нет'}</b>\n\n"
            f"👥 Овнеры бота:\n{owners_text}"
        )
    else:
        # Private chat
        uid = user.id
        role = await get_role(uid)
        await message.answer(
            f"<b>ℹ️ Информация</b>\n\n"
            f"🆔 Ваш ID: <code>{uid}</code>\n"
            f"🎭 Роль: <b>{role}</b>"
        )


@router.message(F.text == "🔙 Главное меню")
async def back_to_main(message: Message):
    role = await get_role(message.from_user.id)
    is_root = role == "root"
    is_owner = role in ("root", "owner")
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu(is_root=is_root, is_owner=is_owner),
    )


@router.message(F.text == "📋 Админ панель")
async def admin_panel_entry(message: Message):
    if message.from_user.id != ROOT_ID:
        return await message.answer("⛔ Нет доступа.")
    await message.answer("🛠 Админ-панель:", reply_markup=admin_panel_kb())


@router.message(F.text == "📊 Логи рассылок")
async def logs_menu_entry(message: Message):
    role = await get_role(message.from_user.id)
    if role not in ("root", "owner"):
        return await message.answer("⛔ Нет доступа.")
    await message.answer("📊 Логи рассылок:", reply_markup=logs_menu_kb())
