from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LinkPreviewOptions, Message
from aiogram.enums import ChatType

from hav_bot.config import Settings
from hav_bot.handlers.apply import Apply
from hav_bot.keyboards import main_menu

router = Router(name="menu")

MENU_TEXT = (
    "HAV — хмарна архітектура, ERP, BAS і Odoo.\n"
    "Оберіть напрямок або залиште заявку кнопкою нижче."
)


def _private(message: Message) -> bool:
    return message.chat.type == ChatType.PRIVATE


async def show_menu(message: Message, settings: Settings) -> None:
    await message.answer(
        MENU_TEXT,
        reply_markup=main_menu(settings.site_url),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


@router.message(CommandStart())
@router.message(Command("help"))
async def menu(message: Message, settings: Settings, state: FSMContext) -> None:
    if not _private(message):
        return
    await state.clear()
    await show_menu(message, settings)


@router.message(Command("cancel"))
async def cancel(message: Message, settings: Settings, state: FSMContext) -> None:
    if not _private(message):
        return
    current = await state.get_state()
    await state.clear()
    if current is None:
        await message.answer("Немає активної заявки.")
        return
    await message.answer("Заявку скасовано.")
    await show_menu(message, settings)


@router.callback_query(F.data == "menu:apply")
async def begin(query: CallbackQuery, state: FSMContext) -> None:
    message = query.message
    if message is None or message.chat.type != ChatType.PRIVATE:
        await query.answer()
        return
    await state.set_state(Apply.name)
    await state.set_data({})
    await message.answer("Як до вас звертатись?")
    await query.answer()
