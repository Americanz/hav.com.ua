from aiogram.types import LinkPreviewOptions

from hav_bot.config import Settings
from hav_bot.keyboards import lead_keyboard
from hav_bot.leads import build_text


async def publish_lead(bot, settings: Settings, lead: dict, *, source: str) -> None:
    if not settings.configured:
        raise RuntimeError("telegram is not configured")
    await bot.send_message(
        settings.chat_id,
        build_text(lead, source=source),
        reply_markup=lead_keyboard(lead, settings.site_url),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
