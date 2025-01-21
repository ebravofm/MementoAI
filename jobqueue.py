from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, Defaults
from telegram.ext import Defaults
from telegram import Update

from ptbcontrib.ptb_jobstores.sqlalchemy import PTBSQLAlchemyJobStore

from datetime import datetime, timedelta, time
from utils import transcribe_voice, logger, tz

from agent import reminder_from_prompt, reminder_to_text
from config import TG_TOKEN, DATABASE_URL

from notifications import notify_next_day_jobs_callback, schedule_daily_notification

from collections import defaultdict


Defaults.tzinfo = tz



# Define a few command handlers. These usually take the two arguments update and
# context.
# Best practice would be to replace context with an underscore,
# since context is an unused local variable.
# This being an example and not having context present confusing beginners,
# we decided to have it present as context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text("Hi! Use /set <seconds> to set a timer")


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


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)


async def set_reminder_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles both audio and text messages to set a reminder timer."""
    logger.info("Reminder received")
    chat_id = update.effective_message.chat_id

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

        
async def audio_handling(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    logger.info("Audio received")
    voice_file = await context.bot.get_file(update.message.voice.file_id)

    transcription = await transcribe_voice(voice_file)
    # reminder = reminder_from_prompt(transcription)
    
    return transcription


async def list_jobs(update, context):
    """Lists all scheduled jobs in the JobQueue grouped by day."""
    # Obtener todos los trabajos de la JobQueue
    jobs = context.job_queue.jobs()

    if not jobs:
        await update.message.reply_text("No jobs are currently scheduled.")
        return

    # Agrupar trabajos por día
    jobs_by_day = defaultdict(list)
    for job in jobs:
        if job.data and "Time" in job.data and "Title" in job.data:
            job_day = job.next_run_time.date()
            jobs_by_day[job_day].append(job)

    # Formatear la lista de trabajos por día
    message = "Scheduled Jobs:\n"
    for day, jobs in sorted(jobs_by_day.items()):
        day_str = day.strftime("%A %d %B")  # Ejemplo: Tuesday 23 January 2025
        message += f"\n{day_str}:\n"
        message += "\n".join(
            [f"  - {job.data['Time'].strftime('%H:%M')}: {job.data['Title']}" for job in jobs]
        )
        message += "\n"

    # Enviar el mensaje al usuario
    await update.message.reply_text(message)    

async def list_jobs_for_week(update, context, start_date: datetime):
    """Lists all scheduled jobs for the remaining days of the week in the JobQueue."""
    # Get all jobs from the JobQueue
    jobs = context.job_queue.jobs()

    if not jobs:
        await update.message.reply_text("No jobs are currently scheduled.")
        return

    # Define the start of the remaining week (start_date) and end of the week (Sunday)
    today = datetime.now()
    start_of_remaining_week = max(today, start_date)
    end_date = start_of_remaining_week + timedelta(days=(6 - start_of_remaining_week.weekday()))

    # Filter jobs for the remaining days of the week
    jobs_for_week = [
        job for job in jobs
        if start_of_remaining_week.date() <= job.next_run_time.date() <= end_date.date()
    ]

    if not jobs_for_week:
        await update.message.reply_text(
            f"No jobs scheduled for the remaining week from {start_of_remaining_week.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}.")
        return

    # Format the job list
    job_list = "\n".join([f"- {job.name} ({job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')})" for job in jobs_for_week])

    await update.message.reply_text(
        f"Jobs for the remaining week from {start_of_remaining_week.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}:\n{job_list}")


    
async def list_jobs_for_day(update, context, target_date: datetime):
    """Lists all scheduled jobs for a specific day in the JobQueue."""
    # Get all jobs from the JobQueue
    jobs = context.job_queue.jobs()

    if not jobs:
        await update.message.reply_text("No jobs are currently scheduled.")
        return

    # Filter jobs for the specific day
    jobs_for_day = [
        job for job in jobs
        if job.next_run_time.date() == target_date.date() and job.data is not None
    ]

    if not jobs_for_day:
        await update.message.reply_text(f"No jobs scheduled for {target_date.strftime('%Y-%m-%d')}.")
        return

    # Format the job list
    job_list = "\n".join([f"{job.data['Time'].strftime('%H:%M')}: {job.data['Title']}" for job in jobs_for_day])

    await update.message.reply_text(f"*Recordatorios para el {target_date.strftime('%d/%m')}:*\n\n{job_list}", parse_mode="markdown")


async def list_jobs_for_current_day(update, context):
    """Lists all scheduled jobs for the current day."""
    await list_jobs_for_day(update, context, datetime.now())


async def list_jobs_for_next_day(update, context):
    """Lists all scheduled jobs for the next day."""
    next_day = datetime.now() + timedelta(days=1)
    await list_jobs_for_day(update, context, next_day)


async def list_jobs_for_current_week(update, context):
    """Lists all scheduled jobs for the current week."""
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    await list_jobs_for_week(update, context, start_of_week)


async def list_jobs_for_next_week(update, context):
    """Lists all scheduled jobs for the next week."""
    today = datetime.now()
    start_of_next_week = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
    await list_jobs_for_week(update, context, start_of_next_week)
    



def main() -> None:
    """Run bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TG_TOKEN).build()

    application.job_queue.scheduler.add_jobstore(
        PTBSQLAlchemyJobStore(
            application=application,
            url=DATABASE_URL,
            )
    )
    
    schedule_daily_notification(
        job_queue=application.job_queue,
        callback=notify_next_day_jobs_callback,
        job_name="notify_next_day_jobs"
    )
    # job_minute = job_queue.run_repeating(callback_minute, interval=60, first=10)

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("unset", unset))
    application.add_handler(CommandHandler("list", list_jobs))
    application.add_handler(MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), set_reminder_timer))
    application.add_handler(CommandHandler("list_day", list_jobs_for_current_day))
    application.add_handler(CommandHandler("list_next_day", list_jobs_for_next_day))
    application.add_handler(CommandHandler("list_week", list_jobs_for_current_week))
    application.add_handler(CommandHandler("list_next_week", list_jobs_for_next_week))


    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    



if __name__ == "__main__":
    main()