from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from menu_constants import (
    MENU,
    ADD,
    SHOW,
    DELETE,
    ADD_PERIODIC,
    LISTENING_REMINDER,
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
    START_OVER,
    START_WITH_NEW_REPLY,
    STOPPING,
    MESSAGE_TEXT,
    END
)

from menu_functions import (
    echo,
    start,
    add_reminder_timer,
    show_all,
    show_today,
    show_tomorrow,
    show_week,
    show_by_name,
    confirm_delete_all,
    delete_all,
    confirm_delete_by_name,
    delete_by_name,
    categorize_and_reply
)

from ptbcontrib.ptb_jobstores.sqlalchemy import PTBSQLAlchemyJobStore
from ptbcontrib.postgres_persistence import PostgresPersistence
from handlers.categorize import select_job_by_name
from handlers.jobs import filter_jobs
from utils.logger import logger
from config import TG_TOKEN, DATABASE_URL


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


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "❌ *Eliminar Recordatorios* ❌\n\n¿Qué recordatorios quieres eliminar?\n_Selec. la opción que desees_."
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="🚮 Borrar todos los recordatorios", callback_data=str(DELETE_ALL)),
            InlineKeyboardButton(text="🔍 Borrar recordatorio específico", callback_data=str(DELETE_BY_NAME)),
        ],
        [
            InlineKeyboardButton(text="⬅️ Atrás", callback_data=str(END)),
        ],
    ])
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="markdown")
    return DELETE


async def listening_to_delete_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "*¿Cual es el recordatorio que deseas borrar?*"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Cancelar", callback_data=str(END))]
    ])
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="markdown")
    return LISTENING_TO_DELETE_BY_NAME    


async def end_second_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[START_OVER] = True
    await start(update, context)
    return MENU


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Okay, bye.")
    return END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    text = "See you around!"
    await update.callback_query.edit_message_text(text=text)
    return END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    try:
        await update.callback_query.message.reply_text("Se produjo un error, volviendo al menú principal.")
    except AttributeError:
        await update.effective_message.reply_text("Se produjo un error, volviendo al menú principal.")
    
    # Limpiar el estado y volver al menú principal
    context.user_data['START_OVER'] = True
    context.user_data['START_WITH_NEW_REPLY'] = True
    context.user_data['MESSAGE_TEXT'] = None
    
    await start(update, context)

def main() -> None:
    application = Application.builder().token(TG_TOKEN).persistence(PostgresPersistence(url=DATABASE_URL)).build()
    
    application.job_queue.scheduler.add_jobstore(
        PTBSQLAlchemyJobStore(
            application=application,
            url=DATABASE_URL,
            )
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
            LISTENING_PERIODIC_REMINDER: [MessageHandler(filters.VOICE | (filters.TEXT & ~filters.COMMAND), echo)],
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