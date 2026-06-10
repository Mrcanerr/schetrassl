from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu(is_root: bool = False, is_owner: bool = False) -> ReplyKeyboardMarkup:
    buttons = []
    if is_root:
        buttons.append([KeyboardButton(text="📋 Админ панель")])
    if is_root or is_owner:
        buttons.append([KeyboardButton(text="📨 Создать рассылку")])
        buttons.append([KeyboardButton(text="📑 Мои рассылки")])
        buttons.append([KeyboardButton(text="📊 Логи рассылок")])
    buttons.append([KeyboardButton(text="ℹ️ Info")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def admin_panel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить овнера"), KeyboardButton(text="➖ Удалить овнера")],
            [KeyboardButton(text="➕ Добавить группу"), KeyboardButton(text="➖ Удалить группу")],
            [KeyboardButton(text="📋 Список овнеров"), KeyboardButton(text="📋 Список групп")],
            [KeyboardButton(text="🔙 Главное меню")],
        ],
        resize_keyboard=True,
    )


def logs_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📤 Отправленные рассылки")],
            [KeyboardButton(text="🗑 Удалённые рассылки")],
            [KeyboardButton(text="🔙 Главное меню")],
        ],
        resize_keyboard=True,
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


def broadcasts_inline(broadcasts: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for bc in broadcasts:
        builder.row(
            InlineKeyboardButton(
                text=f"📢 {bc['name']}",
                callback_data=f"bc_view:{bc['id']}",
            )
        )
    return builder.as_markup()


def broadcast_actions_kb(broadcast_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Изменить", callback_data=f"bc_edit:{broadcast_id}"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"bc_delete:{broadcast_id}"),
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="bc_list")],
        ]
    )


def confirm_delete_kb(broadcast_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"bc_confirm_del:{broadcast_id}"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"bc_view:{broadcast_id}"),
            ]
        ]
    )
