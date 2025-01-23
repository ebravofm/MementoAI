from telegram.ext import ContextTypes
from telegram import Update
from telegram.constants import ChatAction

from datetime import datetime, timedelta

from utils.agents import reminder_from_prompt, reminder_to_text
from utils.logger import logger, tz
from utils.transcriptions import audio_handling
from handlers.jobs import remove_job_if_exists


async def set_reminder_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles both audio and text messages to set a reminder timer."""
    logger.info("Reminder received")

    chat_id = update.effective_message.chat_id
    await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

    # Determine the message type (audio or text)
    if update.message.voice:  # Audio message
        transcription = await audio_handling(update, context)  # Convert audio to text
    else:  # Text message
        transcription = update.message.text

    # Generate reminder from the text
    reminder = reminder_from_prompt(transcription)
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
            await update.effective_message.reply_text("Sorry, we cannot go back to the future!")
            return

        # Remove existing jobs with the same name and add the new one
        job_removed = remove_job_if_exists(timer_name, context)
        
        context.job_queue.run_once(
            alarm,
            when=timer_date,
            chat_id=chat_id,
            name=timer_name,
            data=reminder,
        )
        
        context.job_queue.run_once(
            alarm_minus_30,
            when=timer_date - timedelta(minutes=30),
            chat_id=chat_id,
            name=f"{timer_name} -30",
            data=reminder,
        )


        # Confirmation message
        text = f"Timer successfully set for {timer_name}!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError) as e:
        await update.effective_message.reply_text(f"An error occurred: {str(e)}")



async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    logger.info(f"Alarm triggered for chat_id {job.chat_id} with data: {job.data['text']}")
    await context.bot.send_message(job.chat_id, text=job.data['text'], parse_mode="markdown")


async def alarm_minus_30(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    logger.info(f"Alarm triggered for chat_id {job.chat_id} with data: {job.data['text']}")
    
    text = 'Faltan *30 minutos* para:\n' + job.data['Title']
    
    await context.bot.send_message(job.chat_id, text=text, parse_mode="markdown")
