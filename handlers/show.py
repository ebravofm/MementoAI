from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from functions.jobs import filter_jobs, print_jobs
from utils.constants import (
    SHOW,
    SHOW_ALL,
    SHOW_TODAY,
    SHOW_TOMORROW,
    SHOW_WEEK,
    SHOW_BY_NAME,
    END,
    MENU,
    BACK
)

from datetime import datetime, timedelta

from texts.texts import (
    TXT_SHOW,
    TXT_BUTTON_SHOW_ALL,
    TXT_BUTTON_SHOW_TODAY,
    TXT_BUTTON_SHOW_TOMORROW,
    TXT_BUTTON_SHOW_BY_NAME,
    TXT_BUTTON_SHOW_WEEK,
    TXT_BUTTON_BACK,
    TXT_NO_REMINDERS_SCHEDULED,
    TXT_SHOW_TODAY_HEADER,
    TXT_SHOW_TOMORROW_HEADER,
    TXT_SHOW_WEEK_HEADER,
    TXT_SHOW_ALL_HEADER,
    TXT_BUTTON_CONTINUE
)

from handlers.misc import send_message, continue_keyboard, hide_keyboard

import locale
locale.setlocale(locale.LC_TIME, "es_ES")


async def show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = TXT_SHOW
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text=TXT_BUTTON_SHOW_ALL, callback_data=str(SHOW_ALL)),
        ],
        [
            InlineKeyboardButton(text=TXT_BUTTON_SHOW_TODAY, callback_data=str(SHOW_TODAY)),
        ],
        [
            InlineKeyboardButton(text=TXT_BUTTON_SHOW_TOMORROW, callback_data=str(SHOW_TOMORROW)),
            InlineKeyboardButton(text=TXT_BUTTON_SHOW_WEEK, callback_data=str(SHOW_WEEK)),
        ],
        [
            InlineKeyboardButton(text=TXT_BUTTON_BACK, callback_data=str(BACK)),
        ],
    ])
    await send_message(update, context, text=text, keyboard=keyboard, edit=True)
    return SHOW


async def show_all(update, context, start_date: datetime = None, end_date: datetime = None, header=TXT_SHOW_ALL_HEADER, show_periodic=True):
    """Lists all scheduled jobs in the JobQueue grouped by day."""
    
    chat_id = update.effective_chat.id

    jobs = filter_jobs(context.job_queue, chat_id=chat_id, job_type='parent', start_date=start_date, end_date=end_date)

    if not jobs:
        msg = await send_message(update, context, text=TXT_NO_REMINDERS_SCHEDULED, keyboard=continue_keyboard, edit=True)
        
    else:    
        response_for_user = print_jobs(jobs, show_periodic=True)
        msg = await send_message(update, context, text=response_for_user, edit=True, keyboard=continue_keyboard)

    await hide_keyboard(update, context, msg=msg)        
    

async def show_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show today's reminders."""
    today = datetime.now()
    await show_all(update, context, start_date=today, end_date=today, header=TXT_SHOW_TODAY_HEADER, show_periodic=False)
    
    
async def show_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show tomorrow's reminders."""
    tomorrow = datetime.now() + timedelta(days=1)
    await show_all(update, context, start_date=tomorrow, end_date=tomorrow, header=TXT_SHOW_TOMORROW_HEADER, show_periodic=False)
    return MENU


async def show_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show reminders for the next 7 days."""
    today = datetime.now()
    await show_all(update, context, start_date=today, end_date=today + timedelta(days=7), header=TXT_SHOW_WEEK_HEADER, show_periodic=False)
    return MENU
