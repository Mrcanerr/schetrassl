from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database as db
from keyboards import main_menu, cancel_kb
from utils import get_role, parse_hours, hours_to_str
from scheduler import schedule_broadcast

router = Router()


class CreateBroadcast(StatesGroup):
    text = State()
    hours = State()
    name = State()


class EditBroadcast(StatesGroup):
    text = State()
    hours = State()
    name = State()


async def _can_manage(user_id: int) -> bool:
    role = await get_role(user_id)
    return role in ("root", "owner")


def _menu(role: str):
    return main_menu(role == "root", role in ("root", "owner"))


# ─── CREATE ───────────────────────────────────────────────────────────────

@router.message(F.text == "📨 Создать рассылку")
async def start_create(message: Message, state: FSMContext):
    if not await _can_manage(message.from_user.id):
        return await message.answer("⛔ Нет доступа.")
    await state.set_state(CreateBroadcast.text)
    await message.answer(
        "✏️ <b>Шаг 1/3</b>\nВведите текст рассылки:",
        reply_markup=cancel_kb(),
    )


@router.message(CreateBroadcast.text)
async def create_get_text(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        role = await get_role(message.from_user.id)
        return await message.answer("Отменено.", reply_markup=_menu(role))
    await state.update_data(text=message.text)
    await state.set_state(CreateBroadcast.hours)
    await message.answer(
        "🕐 <b>Шаг 2/3</b>\nВведите часы отправки (МСК) через запятую:\n"
        "Пример: <code>9,12,15,18</code>"
    )


@router.message(CreateBroadcast.hours)
async def create_get_hours(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        role = await get_role(message.from_user.id)
        return await message.answer("Отменено.", reply_markup=_menu(role))
    hours = parse_hours(message.text)
    if hours is None:
        return await message.answer("❗ Неверный формат. Пример: <code>9,12,15,18</code>")
    await state.update_data(hours=hours_to_str(hours))
    await state.set_state(CreateBroadcast.name)
    await message.answer("📌 <b>Шаг 3/3</b>\nВведите название рассылки:")


@router.message(CreateBroadcast.name)
async def create_get_name(
    message: Message,
    state: FSMContext,
    scheduler: AsyncIOScheduler,
    broadcast_bot,
):
    if message.text == "❌ Отмена":
        await state.clear()
        role = await get_role(message.from_user.id)
        return await message.answer("Отменено.", reply_markup=_menu(role))

    data = await state.get_data()
    name = message.text.strip()
    bc_id = await db.create_broadcast(
        name=name,
        text=data["text"],
        hours=data["hours"],
        created_by=message.from_user.id,
    )
    await state.clear()

    # Schedule immediately without restart
    bc = await db.get_broadcast(bc_id)
    schedule_broadcast(scheduler, broadcast_bot, bc)

    role = await get_role(message.from_user.id)
    hours_display = ", ".join(h + ":00" for h in data["hours"].split(","))
    await message.answer(
        f"✅ Рассылка <b>{name}</b> создана и активирована!\n"
        f"⏰ Время отправки (МСК): {hours_display}",
        reply_markup=_menu(role),
    )


# ─── EDIT ─────────────────────────────────────────────────────────────────

@router.message(EditBroadcast.text)
async def edit_get_text(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        role = await get_role(message.from_user.id)
        return await message.answer("Отменено.", reply_markup=_menu(role))
    await state.update_data(new_text=message.text)
    await state.set_state(EditBroadcast.hours)
    await message.answer(
        "🕐 Введите новые часы отправки (МСК) через запятую:\nПример: <code>9,12,15</code>"
    )


@router.message(EditBroadcast.hours)
async def edit_get_hours(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        role = await get_role(message.from_user.id)
        return await message.answer("Отменено.", reply_markup=_menu(role))
    hours = parse_hours(message.text)
    if hours is None:
        return await message.answer("❗ Неверный формат. Пример: <code>9,12,15</code>")
    await state.update_data(new_hours=hours_to_str(hours))
    await state.set_state(EditBroadcast.name)
    await message.answer("📌 Введите новое название рассылки:")


@router.message(EditBroadcast.name)
async def edit_get_name(
    message: Message,
    state: FSMContext,
    scheduler: AsyncIOScheduler,
    broadcast_bot,
):
    if message.text == "❌ Отмена":
        await state.clear()
        role = await get_role(message.from_user.id)
        return await message.answer("Отменено.", reply_markup=_menu(role))

    data = await state.get_data()
    bc_id = data["edit_broadcast_id"]
    new_name = message.text.strip()
    await db.update_broadcast(bc_id, new_name, data["new_text"], data["new_hours"])
    await state.clear()

    # Re-schedule with new hours
    from scheduler import unschedule_broadcast
    unschedule_broadcast(scheduler, bc_id)
    bc = await db.get_broadcast(bc_id)
    if bc:
        schedule_broadcast(scheduler, broadcast_bot, bc)

    role = await get_role(message.from_user.id)
    await message.answer("✅ Рассылка обновлена!", reply_markup=_menu(role))
