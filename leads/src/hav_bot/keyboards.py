from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from hav_bot.leads import TOPICS


def main_menu(site: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Залишити заявку", callback_data="menu:apply")],
            [
                InlineKeyboardButton(text="ERP", url=f"{site}/erp"),
                InlineKeyboardButton(text="BAS", url=f"{site}/bas"),
                InlineKeyboardButton(text="Odoo", url=f"{site}/odoo"),
            ],
            [
                InlineKeyboardButton(text="Avocado", url=f"{site}/avocado"),
                InlineKeyboardButton(text="Лояльність", url=f"{site}/loyalty"),
            ],
            [InlineKeyboardButton(text="Сайт", url=site)],
        ]
    )


def skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Пропустити", callback_data="apply:skip")]]
    )


def topic_keyboard() -> InlineKeyboardMarkup:
    topics = [name for name in ("ERP", "BAS", "Odoo") if name in TOPICS]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"apply:topic:{name}") for name in topics],
            [
                InlineKeyboardButton(text="Trade", callback_data="apply:topic:Avocado Trade"),
                InlineKeyboardButton(text="Inventory", callback_data="apply:topic:Avocado Inventory"),
            ],
            [InlineKeyboardButton(text="Лояльність", callback_data="apply:topic:Лояльність")],
            [InlineKeyboardButton(text="Інше", callback_data="apply:topic:")],
        ]
    )


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Надіслати", callback_data="apply:send"),
                InlineKeyboardButton(text="Скасувати", callback_data="apply:cancel"),
            ]
        ]
    )


def lead_keyboard(lead: dict, site: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="В роботі", callback_data="lead:work"),
            InlineKeyboardButton(text="Закрито", callback_data="lead:done"),
        ]
    ]
    topic = lead.get("topic") or ""
    pages = {
        "ERP": f"{site}/erp",
        "BAS": f"{site}/bas",
        "Odoo": f"{site}/odoo",
        "Avocado": f"{site}/avocado",
        "Avocado Trade": f"{site}/trade",
        "Avocado Inventory": f"{site}/inventory",
        "Лояльність": f"{site}/loyalty",
    }
    if topic in pages:
        rows.append([InlineKeyboardButton(text=f"Сторінка {topic}", url=pages[topic])])
    return InlineKeyboardMarkup(inline_keyboard=rows)
