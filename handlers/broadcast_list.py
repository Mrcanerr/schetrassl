from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database as db
from keyboards import broadcasts_inline, broadcast_actions_kb, confirm_delete_kb, cancel_kb, main_menu
from utils import get_role
from handlers.broadcast_create import EditBroadcast
from scheduler import unschedule_broadcast

router = Router()


async def _can_manage(user_id: int) -> bool:
    role = await get_role(user_id)
    return role in ("root", "owner")


@router.message(F.text == "📑 Мои рассылки")
async def list_broadcasts(message: Message):
    if not await _can_manage(message.from_user.id):
        return await message.answer("⛔ Нет доступа.")

    role = await get_role(message.from_user.id)
    if role == "root":
        broadcasts = await db.get_broadcasts()
    else:
        broadcasts = await db.get_broadcasts(user_id=message.from_user.id)

    if not broadcasts:
        return await message.answer("ℹ️ Нет активных рассылок.")
    await message.answer(
        f"📑 <b>Рассылки ({len(broadcasts)}):</b>",
        reply_markup=broadcasts_inline(broadcasts),
    )


@router.callback_query(F.data == "bc_list")
async def cb_list(callback: CallbackQuery):
    role = await get_role(callback.from_user.id)
    if role == "root":
        broadcasts = await db.get_broadcasts()
    else:
        broadcasts = await db.get_broadcasts(user_id=callback.from_user.id)

    if not broadcasts:
        await callback.message.edit_text("ℹ️ Нет активных рассылок.")
        return await callback.answer()

    await callback.message.edit_text(
        f"📑 <b>Рассылки ({len(broadcasts)}):</b>",
        reply_markup=broadcasts_inline(broadcasts),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bc_view:"))
async def cb_view(callback: CallbackQuery):
    bc_id = int(callback.data.split(":")[1])
    bc = await db.get_broadcast(bc_id)
    if not bc:
        return await callback.answer("Рассылка не найдена.", show_alert=True)

    role = await get_role(callback.from_user.id)
    if role not in ("root", "owner"):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)

    hours_display = ", ".join(f"{h}:00" for h in bc["hours"].split(","))
    text = (
        f"📢 <b>{bc['name']}</b>\n\n"
        f"📝 Текст:\n{bc['text']}\n\n"
        f"⏰ Время (МСК): {hours_display}\n"
        f"👤 Создатель: <code>{bc['created_by']}</code>\n"
        f"📅 Создана: {bc['created_at'][:16]}"
    )
    await callback.message.edit_text(text, reply_markup=broadcast_actions_kb(bc_id))
    await callback.answer()


@router.callback_query(F.data.startswith("bc_delete:"))
async def cb_delete_confirm(callback: CallbackQuery):
    bc_id = int(callback.data.split(":")[1])
    bc = await db.get_broadcast(bc_id)
    if not bc:
        return await callback.answer("Рассылка не найдена.", show_alert=True)

    role = await get_role(callback.from_user.id)
    if role not in ("root", "owner"):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)

    await callback.message.edit_text(
        f"❓ Удалить рассылку <b>{bc['name']}</b>?",
        reply_markup=confirm_delete_kb(bc_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bc_confirm_del:"))
async def cb_confirm_delete(callback: CallbackQuery, scheduler: AsyncIOScheduler):
    bc_id = int(callback.data.split(":")[1])
    role = await get_role(callback.from_user.id)
    if role not in ("root", "owner"):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)

    await db.delete_broadcast(bc_id, callback.from_user.id)
    unschedule_broadcast(scheduler, bc_id)
    await callback.message.edit_text("✅ Рассылка удалена.")
    await callback.answer("Удалено!")


@router.callback_query(F.data.startswith("bc_edit:"))
async def cb_edit(callback: CallbackQuery, state: FSMContext):
    bc_id = int(callback.data.split(":")[1])
    bc = await db.get_broadcast(bc_id)
    if not bc:
        return await callback.answer("Рассылка не найдена.", show_alert=True)

    role = await get_role(callback.from_user.id)
    if role not in ("root", "owner"):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)

    await state.set_state(EditBroadcast.text)
    await state.update_data(edit_broadcast_id=bc_id)
    await callback.message.answer(
        f"✏️ Редактирование рассылки <b>{bc['name']}</b>\n\n"
        f"Введите новый текст рассылки:",
        reply_markup=cancel_kb(),
    )
    await callback.answer()
