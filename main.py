from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from utils.constants import (
    MENU,
    ADD,
    SHOW,
    DELETE,
    ADD_PERIODIC,
    LISTENING_PERIODIC_REMINDER,
    SHOW_ALL,
    SHOW_TODAY,
    SHOW_TOMORROW,
    SHOW_WEEK,
    SHOW_BY_NAME,
    LISTENING_TO_SHOW_BY_NAME,
    DELETE_ALL,
    DELETE_BY_NAME,
    LISTENING_TO_DELETE_BY_NAME,
    CONFIRM_DELETE_ALL,
    CONFIRMED_DELETE_ALL,
    CONFIRM_DELETE_BY_NAME,
    CONFIRMED_DELETE_BY_NAME,
    END
)

from handlers.delete import delete, confirm_delete_all, delete_all, confirm_delete_by_name, delete_by_name, listening_to_delete_by_name
from handlers.show import show, show_all, show_today, show_tomorrow, show_week, show_by_name, listening_to_show_by_name
from handlers.add import add, add_periodic, add_reminder_timer, add_periodic_reminder_timer
from commands import start, stop, help, error_handler, end_second_level
from handlers.misc import echo, categorize_and_reply

from functions.notifications import notify_next_day_jobs_callback, schedule_daily_notification
from ptbcontrib.ptb_jobstores.sqlalchemy import PTBSQLAlchemyJobStore
from ptbcontrib.postgres_persistence import PostgresPersistence

from config import TG_TOKEN, DATABASE_URL


def main() -> None:
    application = Application.builder().token(TG_TOKEN).persistence(PostgresPersistence(url=DATABASE_URL)).build()
    
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
    
    conv_handler = ConversationHandler(
        entry_points= [CommandHandler("start", start), CommandHandler("menu", start)],
        states={
            MENU: [
                CallbackQueryHandler(add, pattern=f"^{str(ADD)}$"),
                CallbackQueryHandler(show, pattern=f"^{str(SHOW)}$"),
                CallbackQueryHandler(delete, pattern=f"^{str(DELETE)}$"),
                CallbackQueryHandler(show_all, pattern=f"^{str(SHOW_ALL)}$"),
                CallbackQueryHandler(show_today, pattern=f"^{str(SHOW_TODAY)}$"),
                CallbackQueryHandler(show_tomorrow, pattern=f"^{str(SHOW_TOMORROW)}$"),
                CallbackQueryHandler(show_week, pattern=f"^{str(SHOW_WEEK)}$"),
                CallbackQueryHandler(show_by_name, pattern=f"^{str(SHOW_BY_NAME)}$"),
                MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), categorize_and_reply),
            ],
            ADD: [
                CallbackQueryHandler(add_periodic, pattern=f"^{str(ADD_PERIODIC)}$"),
                MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), add_reminder_timer),
            ],
            LISTENING_PERIODIC_REMINDER: [MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), add_periodic_reminder_timer)],
            SHOW: [
                CallbackQueryHandler(show_all, pattern=f"^{str(SHOW_ALL)}$"),
                CallbackQueryHandler(show_today, pattern=f"^{str(SHOW_TODAY)}$"),
                CallbackQueryHandler(show_tomorrow, pattern=f"^{str(SHOW_TOMORROW)}$"),
                CallbackQueryHandler(show_week, pattern=f"^{str(SHOW_WEEK)}$"),
                CallbackQueryHandler(listening_to_show_by_name, pattern=f"^{str(SHOW_BY_NAME)}$"),
            ],
            LISTENING_TO_SHOW_BY_NAME: [MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), show_by_name)],
            DELETE: [
                CallbackQueryHandler(confirm_delete_all, pattern=f"^{str(DELETE_ALL)}$"),
                CallbackQueryHandler(listening_to_delete_by_name, pattern=f"^{str(DELETE_BY_NAME)}$"),
            ],
            CONFIRM_DELETE_ALL: [
                CallbackQueryHandler(delete_all, pattern=f"^{str(CONFIRMED_DELETE_ALL)}$"),
            ],
            LISTENING_TO_DELETE_BY_NAME: [MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), confirm_delete_by_name)],
            CONFIRM_DELETE_BY_NAME: [
                CallbackQueryHandler(delete_by_name, pattern=f"^{str(CONFIRMED_DELETE_BY_NAME)}$"),
            ],
        },
        fallbacks=[
            CommandHandler("stop", stop),
            CommandHandler("menu", start),
            CommandHandler("start", start),
            CommandHandler("help", help),
            CallbackQueryHandler(end_second_level, pattern=f"^{str(END)}$"),
            # CallbackQueryHandler(start, pattern=f"^{str(MENU)}$"),
            CallbackQueryHandler(delete_all, pattern=f"^{str(CONFIRMED_DELETE_ALL)}$"),
            CallbackQueryHandler(delete_by_name, pattern=f"^{str(CONFIRMED_DELETE_BY_NAME)}$"),
        ],
    )
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
    
    
# TODO:
# - Add periodic reminders
# - multilanguage support
# - Add tests
# al mostrar todos los recordatorios, distinguir entre run=once y run=periodic