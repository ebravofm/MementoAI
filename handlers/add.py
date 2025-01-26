from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils.misc import cleanup_and_restart, handle_audio_or_text
from utils.agents import reminder_from_prompt, reminder_to_text
from functions.notifications import alarm, alarm_minus_30
from functions.jobs import remove_job_if_exists
from utils.logger import logger, tz
from utils.constants import (
    ADD,
    ADD_PERIODIC,
    END,
    LISTENING_PERIODIC_REMINDER,
    MESSAGE_TEXT,
    MENU
)

from datetime import datetime, timedelta


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "📅 *Nuevo Recordatorio* 📅\n\n¿Qué recordatorio quieres agregar? \[📝/🎙️]\nIncluye fecha, hora y lugar. \n\n_(Si es périódico, selecciona opción correspondiente)_"
    keyboard = InlineKeyboardMarkup([
        [
        InlineKeyboardButton(text="🕒️ Recordatorio Periódico", callback_data=str(ADD_PERIODIC)),
        InlineKeyboardButton(text="⬅️ Atrás", callback_data=str(END)),
        ]
    ])
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="markdown")
    return ADD


async def add_periodic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "Por favor, escribe el recordatorio que deseas agregar."
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Atrás", callback_data=str(END))]
    ])
    await update.callback_query.edit_message_text(text=text, parse_mode="markdown", reply_markup=keyboard)
    return LISTENING_PERIODIC_REMINDER


@cleanup_and_restart
async def add_reminder_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    await handle_audio_or_text(update, context)
    query = context.user_data.get(MESSAGE_TEXT)

    logger.info(f"Test: {query}")

    chat_id = update.effective_chat.id
    # Generate reminder from the text
    reminder = reminder_from_prompt(query)
    reminder['chat_id'] = chat_id

    logger.info(f"Reminder: {reminder}")

    # Convert the reminder time to a localized datetime object
    timer_date = reminder['Time'].replace(tzinfo=None)
    timer_date = tz.localize(timer_date)
    timer_date_string = timer_date.strftime("%H:%M %d/%m/%Y")

    timer_name = f"{reminder['Title']} ({timer_date_string})"
    reminder['text'] = reminder_to_text(reminder)

    try:
        # Calculate the time remaining in seconds
        now = datetime.now(tz)
        seconds_until_due = (timer_date - now).total_seconds()

        # Check if the time is in the past
        if seconds_until_due <= 0:
            await update.effective_message.reply_text("No es posible programar recordatorios en el pasado.")
            return

        # Remove existing jobs with the same name and add the new one
        job_removed = remove_job_if_exists(timer_name, context)
        reminder['type'] = 'parent'
        
        context.job_queue.run_once(
            alarm,
            when=timer_date,
            chat_id=chat_id,
            name=timer_name,
            data=reminder,
        )
        
        reminder['type'] = '-30'
        context.job_queue.run_once(
            alarm_minus_30,
            when=timer_date - timedelta(minutes=30),
            chat_id=chat_id,
            name=timer_name,
            data=reminder,
        )

        # Confirmation message
        await update.effective_message.reply_text('Se agendó el siguiente recordatorio:', parse_mode="markdown")
        await update.effective_message.reply_text(reminder['text'], parse_mode="markdown")
        

    except (IndexError, ValueError) as e:
        await update.effective_message.reply_text(f"An error occurred: {str(e)}")
                
    return MENU

