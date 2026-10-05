from __future__ import annotations

import asyncio

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from hav_bot.api import create_app
from hav_bot.config import Settings
from hav_bot.handlers import apply, menu, status
from hav_bot.notify import publish_lead


def build_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(status.router)
    dispatcher.include_router(menu.router)
    dispatcher.include_router(apply.router)
    return dispatcher


async def run() -> None:
    settings = Settings.from_env()
    bot = (
        Bot(settings.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        if settings.token
        else None
    )

    async def publish(lead: dict) -> None:
        await publish_lead(bot, settings, lead, source="сайт")

    app = create_app(publish, configured=settings.configured)
    runner = web.AppRunner(app)
    await runner.setup()
    try:
        await web.TCPSite(runner, "0.0.0.0", settings.port).start()
        print(f"leads listening on {settings.port}", flush=True)
        if bot is None:
            print("telegram env is not set", flush=True)
            await asyncio.Event().wait()
            return
        dispatcher = build_dispatcher()
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Меню"),
                BotCommand(command="help", description="Що вміє бот"),
                BotCommand(command="cancel", description="Скасувати заявку"),
            ],
            scope=BotCommandScopeAllPrivateChats(),
        )
        await dispatcher.start_polling(bot, settings=settings)
    finally:
        await runner.cleanup()
        if bot is not None:
            await bot.session.close()


def main() -> None:
    asyncio.run(run())
