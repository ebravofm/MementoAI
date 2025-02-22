from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils.misc import handle_audio_or_text, reminder_to_text
from utils.agents import reminder_from_prompt, periodic_reminder_from_prompt
from functions.notifications import alarm, alarm_minus_30
from functions.jobs import remove_job_if_exists
from utils.logger import logger, tz
from handlers.misc import send_message

from utils.constants import (
    ADD,
    ADD_PERIODIC,
    END,
    LISTENING_PERIODIC_REMINDER,
    MESSAGE_TEXT,
    MENU
)

from texts.texts import (
    TXT_NEW_REMINDER,
    TXT_BUTTON_PERIODIC_REMINDER,
    TXT_BUTTON_BACK,
    TXT_ADD_PERIODIC_REMINDER,
    TXT_NOT_ABLE_TO_SCHEDULE_PAST,
    TXT_REMINDER_SCHEDULED,
    TXT_ERROR,
    TXT_PROCESSING,
    TXT_BUTTON_CONTINUE
)

from datetime import datetime, timedelta


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = TXT_NEW_REMINDER
    keyboard = InlineKeyboardMarkup([
        [
        InlineKeyboardButton(text=TXT_BUTTON_PERIODIC_REMINDER, callback_data=str(ADD_PERIODIC)),
        InlineKeyboardButton(text=TXT_BUTTON_BACK, callback_data=str(END)),
        ]
    ])
    await send_message(update, context, text=text, keyboard=keyboard, edit=True)
    return ADD


async def add_periodic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = TXT_ADD_PERIODIC_REMINDER
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Atrás", callback_data=str(END))]
    ])
    await send_message(update, context, text=text, keyboard=keyboard, edit=True)
    return LISTENING_PERIODIC_REMINDER


# @cleanup_and_restart
async def add_reminder_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    await handle_audio_or_text(update, context)
    query = context.user_data.get(MESSAGE_TEXT)

    logger.info(f"Test: {query}")

    chat_id = update.effective_chat.id
    # Generate reminder from the text
    # msg = await update.message.reply_text(TXT_PROCESSING)
    
    reminder = reminder_from_prompt(query)
    reminder['chat_id'] = chat_id

    logger.info(f"Reminder: {reminder}")

    # Convert the reminder time to a localized datetime object
    timer_date = reminder['Time'].replace(tzinfo=None)
    timer_date = tz.localize(timer_date)
    timer_date_string = timer_date.strftime("%H:%M %d/%m/%Y")

    timer_name = f"{reminder['Title']} ({timer_date_string})"
    reminder['run'] = 'once'
    reminder['text'] = reminder_to_text(reminder)

    # Calculate the time remaining in seconds
    now = datetime.now(tz)
    seconds_until_due = (timer_date - now).total_seconds()

    # Check if the time is in the past
    if seconds_until_due <= 0:
        await send_message(update, context, text=TXT_NOT_ABLE_TO_SCHEDULE_PAST, edit=True)
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
    await send_message(update, context, text=TXT_REMINDER_SCHEDULED, edit=True)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text=TXT_BUTTON_CONTINUE, callback_data=str(MENU))]
    ])
    await send_message(update, context, text=reminder['text'], keyboard=keyboard)
        
    return MENU


# @cleanup_and_restart
async def add_periodic_reminder_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    await handle_audio_or_text(update, context)
    query = context.user_data.get(MESSAGE_TEXT)

    logger.info(f"Test: {query}")

    chat_id = update.effective_chat.id
    # Generate reminder from the text
    reminder = periodic_reminder_from_prompt(query)
    reminder['chat_id'] = chat_id

    logger.info(f"Reminder: {reminder}")

    # Convert the reminder time to a localized datetime object
    timer_date = reminder['Time'].replace(tzinfo=tz)
    # timer_date = tz.localize(timer_date)
    timer_date_string = timer_date.strftime("%H:%M:%S")

    timer_name = f"{reminder['Title']} ({reminder['Days']})"
    reminder['run'] = 'periodic'
    reminder['text'] = reminder_to_text(reminder)

    # Remove existing jobs with the same name and add the new one
    job_removed = remove_job_if_exists(timer_name, context)
    
    reminder['type'] = 'parent'
    context.job_queue.run_daily(
        alarm,
        time=timer_date,
        days=reminder['Days'],
        chat_id=chat_id,
        name=timer_name,
        data=reminder,
    )

    # Confirmation message
    await send_message(update, context, text=TXT_REMINDER_SCHEDULED)
    await send_message(update, context, text=reminder['text'])
        

    return MENU

