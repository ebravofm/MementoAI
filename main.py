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
    SHOW_ALL,
    SHOW_TODAY,
    SHOW_TOMORROW,
    SHOW_WEEK,
    DELETE,
    DELETE_ALL,
    CONFIRM_DELETE_ALL,
    CONFIRMED_DELETE_ALL,
    CONFIRMED_DELETE_BY_NAME,
    END,
    BACK,
    LISTENING_TO_DELETE_BY_NAME,
    DELETE_BY_NAME
)

from commands import start, error_handler, back_to_menu
from handlers.add import add
from handlers.show import show, show_all, show_today, show_tomorrow, show_week
from handlers.delete import delete, confirm_delete_all, delete_all, delete_by_name, listening_to_delete_by_name
from handlers.main import main_handler, add_handler, show_handler, delete_handler

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
        entry_points= [
            CommandHandler("start", start),
            CommandHandler("menu", start),
            MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), main_handler),
                       ],
        states={
            MENU: [
                CallbackQueryHandler(start, pattern=f"^{str(MENU)}$"),
                CallbackQueryHandler(add, pattern=f"^{str(ADD)}$"),
                CallbackQueryHandler(show, pattern=f"^{str(SHOW)}$"),
                CallbackQueryHandler(delete, pattern=f"^{str(DELETE)}$"),
                CallbackQueryHandler(delete_all, pattern=f"^{str(CONFIRMED_DELETE_ALL)}$"),
                CallbackQueryHandler(delete_by_name, pattern=f"^{str(CONFIRMED_DELETE_BY_NAME)}$"),
                MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), main_handler),
            ],
            ADD: [
                MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), add_handler),
            ],
            SHOW: [
                CallbackQueryHandler(show_all, pattern=f"^{str(SHOW_ALL)}$"),
                CallbackQueryHandler(show_today, pattern=f"^{str(SHOW_TODAY)}$"),
                CallbackQueryHandler(show_tomorrow, pattern=f"^{str(SHOW_TOMORROW)}$"),
                CallbackQueryHandler(show_week, pattern=f"^{str(SHOW_WEEK)}$"),
                # CallbackQueryHandler(listening_to_show_by_name, pattern=f"^{str(SHOW_BY_NAME)}$"),
                MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), show_handler),
            ],
            DELETE: [
                CallbackQueryHandler(confirm_delete_all, pattern=f"^{str(DELETE_ALL)}$"),
                CallbackQueryHandler(listening_to_delete_by_name, pattern=f"^{str(DELETE_BY_NAME)}$"),
                MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), delete_handler),
            ],
            LISTENING_TO_DELETE_BY_NAME: [MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), delete_handler)],
            CONFIRM_DELETE_ALL: [
                CallbackQueryHandler(delete_all, pattern=f"^{str(CONFIRMED_DELETE_ALL)}$"),
            ],
        },
        fallbacks=[
            MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), main_handler),
            CommandHandler("start", start),
            CommandHandler("menu", start),
            CommandHandler("new_reminder", add),
            CallbackQueryHandler(start, pattern=f"^{str(END)}$"),
            CallbackQueryHandler(start, pattern=f"^{str(MENU)}$"),
            CallbackQueryHandler(back_to_menu, pattern=f"^{str(BACK)}$"),
        ],
    )
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
    
    
# TODO:
# - add palceholder for slow responses
# - multilanguage support
# - Add tests
# - agregar recordatorio semanal los domingos en la noche
# vincular a google calendar

# Commands
# menu - Muestra el menú principal de MementoAI
# new_reminder - Registrar un nuevo recordatorio
# new_periodic_reminder - Registrar un nuevo recordatorio periódico
# help - Muestra la ayuda para aprender a utilizar MementoAI