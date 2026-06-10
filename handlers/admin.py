from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import ROOT_ID
import database as db
from keyboards import admin_panel_kb, cancel_kb

router = Router()


class AdminState(StatesGroup):
    add_owner = State()
    remove_owner = State()
    add_group = State()
    remove_group = State()


def root_only(handler):
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id != ROOT_ID:
            return await message.answer("⛔ Только ROOT может это делать.")
        return await handler(message, *args, **kwargs)
    wrapper.__wrapped__ = handler
    return wrapper


# ─── ADD OWNER ────────────────────────────────────────────────────────────

@router.message(F.text == "➕ Добавить овнера")
async def ask_add_owner(message: Message, state: FSMContext):
    if message.from_user.id != ROOT_ID:
        return
    await state.set_state(AdminState.add_owner)
    await message.answer(
        "Введите Telegram ID пользователя, которого хотите сделать овнером:",
        reply_markup=cancel_kb(),
    )


@router.message(AdminState.add_owner)
async def do_add_owner(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено.", reply_markup=admin_panel_kb())
    try:
        uid = int(message.text.strip())
    except ValueError:
        return await message.answer("❗ Введите корректный числовой ID.")
    if uid == ROOT_ID:
        return await message.answer("❗ ROOT уже является хозяином бота.")
    await db.add_owner(uid, None, message.from_user.id)
    await state.clear()
    await message.answer(f"✅ Пользователь <code>{uid}</code> добавлен как овнер.", reply_markup=admin_panel_kb())


# ─── REMOVE OWNER ─────────────────────────────────────────────────────────

@router.message(F.text == "➖ Удалить овнера")
async def ask_remove_owner(message: Message, state: FSMContext):
    if message.from_user.id != ROOT_ID:
        return
    owners = await db.get_owners()
    if not owners:
        return await message.answer("ℹ️ Овнеров нет.", reply_markup=admin_panel_kb())
    text = "Введите Telegram ID овнера для удаления:\n\n"
    text += "\n".join(f"• <code>{o['user_id']}</code> (@{o['username'] or '—'})" for o in owners)
    await state.set_state(AdminState.remove_owner)
    await message.answer(text, reply_markup=cancel_kb())


@router.message(AdminState.remove_owner)
async def do_remove_owner(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено.", reply_markup=admin_panel_kb())
    try:
        uid = int(message.text.strip())
    except ValueError:
        return await message.answer("❗ Введите корректный числовой ID.")
    await db.remove_owner(uid)
    await state.clear()
    await message.answer(f"✅ Овнер <code>{uid}</code> удалён.", reply_markup=admin_panel_kb())


# ─── ADD GROUP ────────────────────────────────────────────────────────────

@router.message(F.text == "➕ Добавить группу")
async def ask_add_group(message: Message, state: FSMContext):
    if message.from_user.id != ROOT_ID:
        return
    await state.set_state(AdminState.add_group)
    await message.answer(
        "Введите данные группы в формате:\n"
        "<code>ID_группы | Название группы</code>\n\n"
        "Пример: <code>-1001234567890 | Моя группа</code>\n\n"
        "Используйте /info в группе, чтобы узнать её ID.",
        reply_markup=cancel_kb(),
    )


@router.message(AdminState.add_group)
async def do_add_group(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено.", reply_markup=admin_panel_kb())
    parts = message.text.split("|", 1)
    if len(parts) != 2:
        return await message.answer("❗ Неверный формат. Пример: <code>-1001234567890 | Моя группа</code>")
    try:
        gid = int(parts[0].strip())
    except ValueError:
        return await message.answer("❗ ID группы должен быть числом.")
    title = parts[1].strip() or "Без названия"
    await db.add_group(gid, title, message.from_user.id)
    await state.clear()
    await message.answer(
        f"✅ Группа <b>{title}</b> (<code>{gid}</code>) добавлена в белый список.",
        reply_markup=admin_panel_kb(),
    )


# ─── REMOVE GROUP ─────────────────────────────────────────────────────────

@router.message(F.text == "➖ Удалить группу")
async def ask_remove_group(message: Message, state: FSMContext):
    if message.from_user.id != ROOT_ID:
        return
    groups = await db.get_groups()
    if not groups:
        return await message.answer("ℹ️ Список групп пуст.", reply_markup=admin_panel_kb())
    text = "Введите ID группы для удаления:\n\n"
    text += "\n".join(f"• <code>{g['group_id']}</code> — {g['title']}" for g in groups)
    await state.set_state(AdminState.remove_group)
    await message.answer(text, reply_markup=cancel_kb())


@router.message(AdminState.remove_group)
async def do_remove_group(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        return await message.answer("Отменено.", reply_markup=admin_panel_kb())
    try:
        gid = int(message.text.strip())
    except ValueError:
        return await message.answer("❗ Введите корректный числовой ID группы.")
    await db.remove_group(gid)
    await state.clear()
    await message.answer(f"✅ Группа <code>{gid}</code> удалена из белого списка.", reply_markup=admin_panel_kb())


# ─── LIST ─────────────────────────────────────────────────────────────────

@router.message(F.text == "📋 Список овнеров")
async def list_owners(message: Message):
    if message.from_user.id != ROOT_ID:
        return
    owners = await db.get_owners()
    if not owners:
        return await message.answer("ℹ️ Овнеров нет.")
    lines = [f"👤 <code>{o['user_id']}</code> | @{o['username'] or '—'} | {o['added_at'][:10]}" for o in owners]
    await message.answer("📋 <b>Список овнеров:</b>\n\n" + "\n".join(lines))


@router.message(F.text == "📋 Список групп")
async def list_groups(message: Message):
    if message.from_user.id != ROOT_ID:
        return
    groups = await db.get_groups()
    if not groups:
        return await message.answer("ℹ️ Список групп пуст.")
    lines = [f"🏠 <code>{g['group_id']}</code> | {g['title']} | {g['added_at'][:10]}" for g in groups]
    await message.answer("📋 <b>Список групп (белый список):</b>\n\n" + "\n".join(lines))
