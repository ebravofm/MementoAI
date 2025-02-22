from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils.misc import handle_audio_or_text
from utils.logger import logger
from utils.agents import select_job_by_name
from functions.jobs import filter_jobs
from utils.constants import (
    SHOW,
    SHOW_ALL,
    SHOW_TODAY,
    SHOW_TOMORROW,
    SHOW_WEEK,
    SHOW_BY_NAME,
    LISTENING_TO_SHOW_BY_NAME,
    END,
    MESSAGE_TEXT,
    MENU    
)

from datetime import datetime, timedelta
from collections import defaultdict

from texts.texts import (
    TXT_SHOW,
    TXT_BUTTON_SHOW_ALL,
    TXT_BUTTON_SHOW_TODAY,
    TXT_BUTTON_SHOW_TOMORROW,
    TXT_BUTTON_SHOW_BY_NAME,
    TXT_BUTTON_SHOW_WEEK,
    TXT_BUTTON_BACK,
    TXT_NO_REMINDERS_SCHEDULED,
    TXT_PERIODIC_REMINDERS,
    TXT_PERIODIC_REMINDERS_DAYS,
    TXT_DAYS_OF_WEEK,
    TXT_SHOW_TODAY_HEADER,
    TXT_SHOW_TOMORROW_HEADER,
    TXT_SHOW_WEEK_HEADER,
    TXT_NO_REMINDER_FOUND,
    TXT_SHOW_ALL_HEADER,
    TXT_BUTTON_CONTINUE
)

from handlers.misc import send_message

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
            InlineKeyboardButton(text=TXT_BUTTON_SHOW_TOMORROW, callback_data=str(SHOW_TOMORROW)),
        ],
        [
            InlineKeyboardButton(text=TXT_BUTTON_SHOW_BY_NAME, callback_data=str(SHOW_BY_NAME)),
            InlineKeyboardButton(text=TXT_BUTTON_SHOW_WEEK, callback_data=str(SHOW_WEEK)),
        ],
        [
            InlineKeyboardButton(text=TXT_BUTTON_BACK, callback_data=str(END)),
        ],
    ])
    # await update.callback_query.answer()
    # await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="markdown")
    await send_message(update, context, text=text, keyboard=keyboard, edit=True)
    return SHOW


async def listening_to_show_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "¿Cual es el recordatorio que deseas ver?"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Cancelar", callback_data=str(END))]
    ])
    # await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    await send_message(update, context, text=text, keyboard=keyboard, edit=True)
    return LISTENING_TO_SHOW_BY_NAME    


# @cleanup_and_restart
async def show_all(update, context, start_date: datetime = None, end_date: datetime = None, header=TXT_SHOW_ALL_HEADER, show_periodic=True):
    """Lists all scheduled jobs in the JobQueue grouped by day."""
    # Filtrar trabajos usando la función filter_jobs
    chat_id = update.effective_chat.id
    jobs = filter_jobs(context, start_date=start_date, end_date=end_date, chat_id=chat_id, job_type='parent')

    if not jobs:
        # try:
        #     await update.callback_query.edit_message_text(TXT_NO_REMINDERS_SCHEDULED)
        # except AttributeError:
        #     await update.effective_message.reply_text(TXT_NO_REMINDERS_SCHEDULED)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=TXT_BUTTON_CONTINUE, callback_data=str(MENU))]
        ])
        await send_message(update, context, text=TXT_NO_REMINDERS_SCHEDULED, keyboard=keyboard, edit=True)
        return MENU

    # Agrupar trabajos por día
    jobs_by_day = defaultdict(list)
    for job in jobs:
        if job.data and "Time" in job.data and "Title" in job.data:
            job_day = job.next_run_time.date()
            jobs_by_day[job_day].append(job)

    # Formatear la lista de trabajos por día
    message = f"📅 *{header}* 📅:\n"
    for day, jobs_ in sorted(jobs_by_day.items()):
        day_str = day.strftime("%A %d/%B") 
        day_str = day_str.title()
        message += f"\n*{day_str}*:\n"
        message += "\n".join(
            [f"    {job.data['Time'].strftime('%H:%M')}: {job.data['Title']}" for job in jobs_]
        )
        message += "\n"
        
    # Mostrar recordatorios periódicos
    if show_periodic and any(job.data['run'] == 'periodic' for job in jobs):
        days_of_week = TXT_DAYS_OF_WEEK
        message += "\n\n"+TXT_PERIODIC_REMINDERS+"\n"
        logger.info(jobs)
        for job in jobs:
            if job.data['run'] == 'periodic':
                logger.info(job.data)
                days = ", ".join(days_of_week[day] for day in job.data['Days']) if len(job.data['Days']) < 7 else TXT_PERIODIC_REMINDERS_DAYS
                message += f"\n    *• {job.data['Title']}* ({days} a las {job.data['Time'].strftime('%H:%M')})"

    # Enviar el mensaje al usuario
    # try:
    #     await update.callback_query.edit_message_text(message, parse_mode="markdown")
    # except AttributeError:
    #     await update.effective_message.reply_text(message, parse_mode="markdown")
    await send_message(update, context, text=message)
        

async def show_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show today's reminders."""
    today = datetime.now()
    await show_all(update, context, start_date=today, end_date=today, header=TXT_SHOW_TODAY_HEADER, show_periodic=False)
    return MENU
    
    
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


# @cleanup_and_restart
async def show_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE, name=None) -> str:
    """Show reminder by name."""
    await handle_audio_or_text(update, context)
    query = context.user_data.get(MESSAGE_TEXT)
    
    if not name:
        name = select_job_by_name(update, context, query)
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type='parent', name=name)
    if not jobs:
        # await update.effective_message.reply_text(TXT_NO_REMINDER_FOUND.format(name=name))
        await send_message(update, context, text=TXT_NO_REMINDER_FOUND.format(name=name))
        
        return

    job = jobs[0]
    
    # await update.effective_message.reply_text(job.data['text'], parse_mode="markdown")
    await send_message(update, context, text=job.data['text'])
