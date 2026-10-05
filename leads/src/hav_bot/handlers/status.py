from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, LinkPreviewOptions, Message

from hav_bot.config import Settings
from hav_bot.leads import with_status

router = Router(name="status")

STATUSES = {"lead:work": "В роботі", "lead:done": "Закрито"}


@router.callback_query(F.data.in_(STATUSES))
async def set_status(query: CallbackQuery, settings: Settings) -> None:
    message = query.message
    if not isinstance(message, Message) or query.data is None:
        await query.answer()
        return
    if str(message.chat.id) != settings.chat_id:
        await query.answer()
        return
    status = STATUSES[query.data]
    try:
        await message.edit_text(
            with_status(message.html_text or message.text or "", status),
            reply_markup=message.reply_markup,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    except TelegramBadRequest:
        await query.answer("Повідомлення не змінилось")
        return
    await query.answer(f"Статус: {status}")
