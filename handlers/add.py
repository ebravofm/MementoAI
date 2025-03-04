from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.misc import send_message, back_keyboard

from utils.constants import (
    ADD,
)

from texts.texts import (
    TXT_NEW_REMINDER,
)

from datetime import datetime, timedelta


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = TXT_NEW_REMINDER
    await send_message(update, context, text=text, keyboard=back_keyboard, edit=True)
    return ADD
