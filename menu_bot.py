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
    DELETE_ALL,
    DELETE_BY_NAME,
    START_OVER,
    START_WITH_NEW_REPLY,
    STOPPING,
    END
)

from menu_functions import (
    echo,
    start,
    show_all,
    show_today,
    show_tomorrow,
    show_week,
    show_by_name,
    delete_all,
    delete_by_name
)

from utils.logger import logger
from config import TG_TOKEN


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "Por favor, escribe el recordatorio que deseas agregar. Si quieres agregar un recordatorio periódico, selecciona la opción correspondiente."
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="Recordatorio Periódico", callback_data=str(ADD_PERIODIC)),
            InlineKeyboardButton(text="Atrás", callback_data=str(END)),
        ]
    ])
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return ADD


async def add_periodic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "Por favor, escribe el recordatorio que deseas agregar."
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Atrás", callback_data=str(END))]
    ])
    await update.callback_query.edit_message_text(text=text, parse_mode="markdown", reply_markup=keyboard)
    return LISTENING_PERIODIC_REMINDER


async def show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "¡Qué recordatorios quieres ver?."
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="Todos los recordatorios", callback_data=str(SHOW_ALL)),
        ],
        [
            InlineKeyboardButton(text="Recordatorios para hoy", callback_data=str(SHOW_TODAY)),
            InlineKeyboardButton(text="Recordatorios para mañana", callback_data=str(SHOW_TOMORROW)),
        ],
        [
            InlineKeyboardButton(text="Recordatorio específico", callback_data=str(SHOW_BY_NAME)),
            InlineKeyboardButton(text="Recordatorios de los próximos 7 días", callback_data=str(SHOW_WEEK)),
        ],
        [
            InlineKeyboardButton(text="Atrás", callback_data=str(END)),
        ],
    ])
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return SHOW


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "Por favor, selecciona la opción que deseas."
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="Borrar todos los recordatorios", callback_data=str(DELETE_ALL)),
            InlineKeyboardButton(text="Borrar recordatorio específico", callback_data=str(DELETE_BY_NAME)),
        ],
        [
            InlineKeyboardButton(text="Atrás", callback_data=str(END)),
        ],
    ])
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return DELETE


async def end_second_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[START_OVER] = True
    await start(update, context)
    return END


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Okay, bye.")
    return END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    text = "See you around!"
    await update.callback_query.edit_message_text(text=text)
    return END


def main() -> None:
    application = Application.builder().token(TG_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
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
            ],
            ADD: [
                CallbackQueryHandler(add_periodic, pattern=f"^{str(ADD_PERIODIC)}$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, echo),
            ],
            LISTENING_PERIODIC_REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, echo)],
            SHOW: [
                CallbackQueryHandler(show_all, pattern=f"^{str(SHOW_ALL)}$"),
                CallbackQueryHandler(show_today, pattern=f"^{str(SHOW_TODAY)}$"),
                CallbackQueryHandler(show_tomorrow, pattern=f"^{str(SHOW_TOMORROW)}$"),
                CallbackQueryHandler(show_week, pattern=f"^{str(SHOW_WEEK)}$"),
                CallbackQueryHandler(show_by_name, pattern=f"^{str(SHOW_BY_NAME)}$"),
            ],
            DELETE: [
                CallbackQueryHandler(delete_all, pattern=f"^{str(DELETE_ALL)}$"),
                CallbackQueryHandler(delete_by_name, pattern=f"^{str(DELETE_BY_NAME)}$"),
            ],
        },
        fallbacks=[
            CommandHandler("stop", stop),
            CallbackQueryHandler(end_second_level, pattern=f"^{str(END)}$"),
        ],
    )
    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()