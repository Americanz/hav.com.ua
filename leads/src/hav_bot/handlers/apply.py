from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, LinkPreviewOptions, Message

from hav_bot.config import Settings
from hav_bot.keyboards import confirm_keyboard, skip_keyboard, topic_keyboard
from hav_bot.leads import EMAIL_RE, check_name, clean, validate
from hav_bot.notify import publish_lead

router = Router(name="apply")


class Apply(StatesGroup):
    name = State()
    email = State()
    phone = State()
    task = State()
    topic = State()
    confirm = State()


def _lead(data: dict) -> tuple[dict | None, str | None]:
    return validate(
        {
            "name": data.get("name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "message": data.get("task"),
            "topic": data.get("topic") or "",
        }
    )


async def _ask_phone(message: Message) -> None:
    await message.answer("Телефон, якщо зручно.", reply_markup=skip_keyboard())


async def _ask_task(message: Message) -> None:
    await message.answer("Коротко опишіть задачу.", reply_markup=skip_keyboard())


async def _ask_topic(message: Message) -> None:
    await message.answer("Який напрямок?", reply_markup=topic_keyboard())


async def _show_confirm(message: Message, data: dict) -> None:
    lead, error = _lead(data)
    if error or lead is None:
        await message.answer(error or "Перевірте дані і почніть спочатку: /cancel")
        return
    from hav_bot.leads import build_text

    await message.answer(
        "Перевірте заявку перед відправкою:\n\n" + build_text(lead, source="бот", status=None),
        reply_markup=confirm_keyboard(),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


@router.message(Apply.name, F.text, ~F.text.startswith("/"))
async def take_name(message: Message, state: FSMContext) -> None:
    name = clean(message.text)
    error = check_name(name)
    if error:
        await message.answer(error)
        return
    await state.update_data(name=name)
    await state.set_state(Apply.email)
    await message.answer("Ваш email?")


@router.message(Apply.email, F.text, ~F.text.startswith("/"))
async def take_email(message: Message, state: FSMContext) -> None:
    email = (message.text or "").strip()
    if not EMAIL_RE.match(email) or len(email) > 120:
        await message.answer("Вкажіть коректний email.")
        return
    await state.update_data(email=email)
    await state.set_state(Apply.phone)
    await _ask_phone(message)


@router.callback_query(StateFilter(Apply.phone, Apply.task), F.data == "apply:skip")
async def skip_optional(query: CallbackQuery, state: FSMContext) -> None:
    message = query.message
    if message is None:
        await query.answer()
        return
    current = await state.get_state()
    if current == Apply.phone.state:
        await state.update_data(phone="")
        await state.set_state(Apply.task)
        await _ask_task(message)
    else:
        await state.update_data(task="")
        await state.set_state(Apply.topic)
        await _ask_topic(message)
    await query.answer()


@router.message(Apply.phone, F.text, ~F.text.startswith("/"))
async def take_phone(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if len(phone) > 40:
        await message.answer("Телефон занадто довгий.")
        return
    await state.update_data(phone=phone)
    await state.set_state(Apply.task)
    await _ask_task(message)


@router.message(Apply.task, F.text, ~F.text.startswith("/"))
async def take_task(message: Message, state: FSMContext) -> None:
    task = (message.text or "").strip()
    if len(task) > 4000:
        await message.answer("Повідомлення занадто довге.")
        return
    await state.update_data(task=task)
    await state.set_state(Apply.topic)
    await _ask_topic(message)


@router.callback_query(Apply.topic, F.data.startswith("apply:topic:"))
async def take_topic(query: CallbackQuery, state: FSMContext) -> None:
    message = query.message
    if message is None or query.data is None:
        await query.answer()
        return
    topic = query.data.removeprefix("apply:topic:")
    await state.update_data(topic=topic)
    await state.set_state(Apply.confirm)
    await _show_confirm(message, await state.get_data())
    await query.answer()


@router.callback_query(Apply.confirm, F.data == "apply:send")
async def send(query: CallbackQuery, state: FSMContext, settings: Settings) -> None:
    message = query.message
    if message is None:
        await query.answer()
        return
    lead, error = _lead(await state.get_data())
    if error or lead is None:
        await query.answer(error or "Перевірте дані.", show_alert=True)
        return
    if not settings.configured:
        await query.answer("Прийом заявок тимчасово недоступний.", show_alert=True)
        return
    try:
        await publish_lead(query.bot, settings, lead, source="бот")
    except Exception as exc:
        print(f"lead send failed: {type(exc).__name__}", flush=True)
        await query.answer("Не вдалося надіслати. Спробуйте ще раз.", show_alert=True)
        return
    await state.clear()
    await message.edit_text("Дякуємо. Заявку надіслано, відповімо протягом 24 годин.")
    await query.answer()


@router.callback_query(F.data == "apply:cancel")
async def cancel_button(query: CallbackQuery, state: FSMContext, settings: Settings) -> None:
    from hav_bot.handlers.menu import show_menu

    message = query.message
    await state.clear()
    if message is not None:
        await message.edit_reply_markup(reply_markup=None)
        await show_menu(message, settings)
    await query.answer("Скасовано")
