from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils.misc import cleanup_and_restart, handle_audio_or_text
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

import locale
locale.setlocale(locale.LC_TIME, "es_ES")


async def show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "📅 *Mostrar Recordatorios* 📅\n\n¿Qué recordatorios quieres ver? \[📝/🎙️]\n_Selec. la opción que desees_."
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="📁 Todos los recordatorios", callback_data=str(SHOW_ALL)),
        ],
        [
            InlineKeyboardButton(text="📆 Hoy", callback_data=str(SHOW_TODAY)),
            InlineKeyboardButton(text="📆 Mañana", callback_data=str(SHOW_TOMORROW)),
        ],
        [
            InlineKeyboardButton(text="🔍 Recordatorio específico", callback_data=str(SHOW_BY_NAME)),
            InlineKeyboardButton(text="📆 Próximos 7 días", callback_data=str(SHOW_WEEK)),
        ],
        [
            InlineKeyboardButton(text="⬅️ Atrás", callback_data=str(END)),
        ],
    ])
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="markdown")
    return SHOW


async def listening_to_show_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "¿Cual es el recordatorio que deseas ver?"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Cancelar", callback_data=str(END))]
    ])
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return LISTENING_TO_SHOW_BY_NAME    


@cleanup_and_restart
async def show_all(update, context, start_date: datetime = None, end_date: datetime = None, header="Recordatorios Programados", show_periodic=True):
    """Lists all scheduled jobs in the JobQueue grouped by day."""
    # Filtrar trabajos usando la función filter_jobs
    chat_id = update.effective_chat.id
    jobs = filter_jobs(context, start_date=start_date, end_date=end_date, chat_id=chat_id, job_type='parent')

    if not jobs:
        try:
            await update.callback_query.edit_message_text("No hay recordatorios programados.")
        except AttributeError:
            await update.effective_message.reply_text("No hay recordatorios programados.")
        return

    # Agrupar trabajos por día
    jobs_by_day = defaultdict(list)
    for job in jobs:
        if job.data and "Time" in job.data and "Title" in job.data:
            job_day = job.next_run_time.date()
            jobs_by_day[job_day].append(job)

    # Formatear la lista de trabajos por día
    message = f"📅 *{header}* 📅:\n"
    for day, jobs in sorted(jobs_by_day.items()):
        day_str = day.strftime("%A %d/%B") 
        day_str = day_str.title()
        message += f"\n*{day_str}*:\n"
        message += "\n".join(
            [f"    {job.data['Time'].strftime('%H:%M')}: {job.data['Title']}" for job in jobs]
        )
        message += "\n"
        
    # Mostrar recordatorios periódicos
    if show_periodic and any(job.data['run'] == 'periodic' for job in jobs):
        days_of_week = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
        message += "\n\n📅 *Recordatorios Periódicos* 📅:\n"
        logger.info(jobs)
        for job in jobs:
            if job.data['run'] == 'periodic':
                logger.info(job.data)
                days = ", ".join(days_of_week[day] for day in job.data['Days']) if len(job.data['Days']) < 7 else "Todos los días"
                message += f"\n    *• {job.data['Title']}* ({days} a las {job.data['Time'].strftime('%H:%M')})"

    # Enviar el mensaje al usuario
    try:
        await update.callback_query.edit_message_text(message, parse_mode="markdown")
    except AttributeError:
        await update.effective_message.reply_text(message, parse_mode="markdown")
        

async def show_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show today's reminders."""
    today = datetime.now()
    await show_all(update, context, start_date=today, end_date=today, header="Recordatorios Programados para Hoy", show_periodic=False)
    return MENU
    
    
async def show_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show tomorrow's reminders."""
    tomorrow = datetime.now() + timedelta(days=1)
    await show_all(update, context, start_date=tomorrow, end_date=tomorrow, header="Recordatorios Programados para Mañana", show_periodic=False)
    return MENU


async def show_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show reminders for the next 7 days."""
    today = datetime.now()
    await show_all(update, context, start_date=today, end_date=today + timedelta(days=7), header="Recordatorios Programados para la Semana", show_periodic=False)
    return MENU


@cleanup_and_restart
async def show_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE, name=None) -> str:
    """Show reminder by name."""
    await handle_audio_or_text(update, context)
    query = context.user_data.get(MESSAGE_TEXT)
    
    if not name:
        name = select_job_by_name(update, context, query)
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type='parent', name=name)
    if not jobs:
        await update.effective_message.reply_text(f"No se encontró el recordatorio '{name}'.")
        
        return

    job = jobs[0]
    
    await update.effective_message.reply_text(job.data['text'], parse_mode="markdown")
