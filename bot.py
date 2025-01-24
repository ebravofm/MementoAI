from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update

from handlers.jobs import list_jobs
from handlers.notifications import notify_next_day_jobs_callback, schedule_daily_notification, delete_callback
from handlers.set_reminders import set_reminder_timer, alarm, alarm_minus_30
from handlers.commands import list_jobs_for_current_day, list_jobs_for_next_day, list_jobs_for_current_week
from handlers.commands import start, categorize_and_reply

from config import TG_TOKEN, DATABASE_URL

from ptbcontrib.ptb_jobstores.sqlalchemy import PTBSQLAlchemyJobStore


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
    application.add_handler(MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), categorize_and_reply))
    application.add_handler(CommandHandler("list_day", list_jobs_for_current_day))
    application.add_handler(CommandHandler("list_next_day", list_jobs_for_next_day))
    application.add_handler(CommandHandler("list_week", list_jobs_for_current_week))
    application.add_handler(CallbackQueryHandler(delete_callback, pattern="^(DELETE_ALL|DELETE_REMINDER.*|CANCELAR)$"))
    
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
# 6. probar que los comandos no afectan otros chat_ids


# TODO:
#     Delete Command
#     List command
#     error handling on agent request, (retry, inform user)