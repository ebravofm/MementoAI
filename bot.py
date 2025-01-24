from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram import Update
from telegram.constants import ParseMode


from handlers.jobs import list_jobs
from handlers.notifications import notify_next_day_jobs_callback, schedule_daily_notification, delete_callback
from handlers.set_reminders import set_reminder_timer, alarm, alarm_minus_30
from handlers.commands import list_jobs_for_current_day, list_jobs_for_next_day, list_jobs_for_current_week
from handlers.commands import start, categorize_and_reply
from utils.logger import logger

from config import TG_TOKEN, DATABASE_URL

from ptbcontrib.ptb_jobstores.sqlalchemy import PTBSQLAlchemyJobStore
import traceback
import html
import json




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
    
    
    application.add_error_handler(error_handler)
    
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=update, text=message, parse_mode=ParseMode.HTML
    )




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