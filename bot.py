from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update

from handlers.jobs import list_jobs, list_jobs_for_current_day, list_jobs_for_next_day, list_jobs_for_current_week, list_jobs_for_next_week
from handlers.notifications import notify_next_day_jobs_callback, schedule_daily_notification
from handlers.reminders import set_reminder_timer, alarm, alarm_minus_30
from handlers.commands import start

from config import TG_TOKEN, DATABASE_URL

from ptbcontrib.ptb_jobstores.sqlalchemy import PTBSQLAlchemyJobStore


# Define a few command handlers. These usually take the two arguments update and
# context.
# Best practice would be to replace context with an underscore,
# since context is an unused local variable.
# This being an example and not having context present confusing beginners,
# we decided to have it present as context.

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
    
    
# TESTS
# 1. send reminder message
# 2. send voice message
# 3. list jobs
# 4. list jobs for day
# 5 wait for reminder


# TODO:
#     Delete Command
#     List command
#     error handling on agent request, (retry, inform user)