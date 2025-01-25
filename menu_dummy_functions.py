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


from utils.logger import logger
from config import TG_TOKEN

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
    START_OVER,
    START_WITH_NEW_REPLY,
    STOPPING,
    END
)


# Top level conversation callbacks
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Selecciona una acción: Agregar recordatorio, mostrar recordatorios o eliminar recordatorios."""
    text = (
        "Puedes elegir agregar un nuevo recordatorio, mostrar los recordatorios o eliminar recordatorios. "
        "Para abortar, simplemente escribe /stop."
    )

    buttons = [
        [
            InlineKeyboardButton(text="Agregar nuevo recordatorio", callback_data=str(ADD)),
            InlineKeyboardButton(text="Mostrar recordatorios", callback_data=str(SHOW)),
        ],
        [
            InlineKeyboardButton(text="Eliminar recordatorios", callback_data=str(DELETE)),
            InlineKeyboardButton(text="Terminar", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we're starting over we don't need to send a new message
    if context.user_data.get(START_OVER):
        if context.user_data.get(START_WITH_NEW_REPLY):
            await context.bot.send_message(update.effective_chat.id, text=text, reply_markup=keyboard)
        else:
            try:
                await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
            except AttributeError:
                await context.bot.send_message(update.effective_chat.id, text=text, reply_markup=keyboard)
    else:
        # await update.message.reply_text(
        #     "Hola! Soy tu asistente de recordatorios. ¿En qué puedo ayudarte hoy?"
        # )
        # await update.message.reply_text(text=text, reply_markup=keyboard)
        await context.bot.send_message(update.effective_chat.id, text="Hola! Soy tu asistente de recordatorios. ¿En qué puedo ayudarte hoy?")
        await context.bot.send_message(update.effective_chat.id, text=text, reply_markup=keyboard)
        

    context.user_data[START_OVER] = False
    context.user_data[START_WITH_NEW_REPLY] = False
    return MENU

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    # await update.message.reply_text(update.message.text)
    # await context.bot.send_message(update.effective_chat.id, text=update.message.text, parse_mode="markdown")
    await update.message.reply_text(update.message.text)
    logger.info(update.message.text)
    
    context.user_data[START_OVER] = True
    await start(update, context)

    return END

async def show_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show all reminders."""
    text = "Mostrando todos los recordatorios."
    await update.callback_query.edit_message_text(text=text, parse_mode="markdown")

    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True

    await start(update, context)

    return END

async def show_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show today's reminders."""
    text = "Mostrando los recordatorios de hoy."
    await update.callback_query.edit_message_text(text=text, parse_mode="markdown")
    
    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True

    await start(update, context)
    return END

async def show_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show tomorrow's reminders."""
    text = "Mostrando los recordatorios de mañana."
    await update.callback_query.edit_message_text(text=text, parse_mode="markdown")

    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True

    await start(update, context)
    return END

async def show_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show reminders for the next 7 days."""
    text = "Mostrando los recordatorios de los próximos 7 días."
    await update.callback_query.edit_message_text(text=text, parse_mode="markdown")

    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True

    await start(update, context)
    return END

async def show_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show reminders by name."""
    text = "Mostrando los recordatorios por nombre."
    await update.callback_query.edit_message_text(text=text, parse_mode="markdown")

    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True

    await start(update, context)
    return END