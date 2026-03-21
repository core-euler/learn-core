import asyncio
import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
FRONTEND_URL = os.getenv("TELEGRAM_AUTH_FRONTEND_URL", "http://localhost:3000").rstrip("/")
LOGIN_CALLBACK_PATH = os.getenv("TELEGRAM_AUTH_CALLBACK_PATH", "/auth/telegram/callback")


def _build_data_check_string(payload: dict[str, str]) -> str:
    return "\n".join(f"{k}={v}" for k, v in sorted(payload.items()))


def _sign_payload(payload: dict[str, str], bot_token: str) -> str:
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    data_check_string = _build_data_check_string(payload)
    return hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()


def build_auth_link(message: Message) -> str:
    if not message.from_user:
        raise RuntimeError("missing_user_in_message")

    user = message.from_user
    payload: dict[str, str] = {
        "id": str(user.id),
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "username": user.username or "",
        "photo_url": "",
        "auth_date": str(int(time.time())),
    }
    payload["hash"] = _sign_payload(payload, BOT_TOKEN)
    return f"{FRONTEND_URL}{LOGIN_CALLBACK_PATH}?{urlencode(payload)}"


async def send_login_message(message: Message) -> None:
    auth_link = build_auth_link(message)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Login to LearnCore", url=auth_link)],
        ]
    )
    await message.answer(
        "Нажмите кнопку ниже, чтобы авторизоваться в LearnCore через Telegram.",
        reply_markup=keyboard,
    )


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start_handler(message: Message) -> None:
        await send_login_message(message)

    @dp.message(Command("login"))
    async def login_handler(message: Message) -> None:
        await send_login_message(message)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
