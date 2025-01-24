#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using nested ConversationHandlers.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
from typing import Any

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

TOKEN = "7788607746:AAF5judrgeu513rNjc1bn-IQAl3b6Q20pmo"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# State definitions for top level conversation
MENU = chr(0)
ADD = chr(1)
SHOW = chr(2)
DELETE = chr(3)
ADD_PERIODIC = chr(4)
LISTENING_REMINDER = chr(5)
LISTENING_PERIODIC_REMINDER = chr(6)
START_OVER = chr(7)
STOPPING = chr(8)
END = ConversationHandler.END

logger.info("MENU: %s, ADD: %s, SHOW: %s, DELETE: %s, END: %s", MENU, ADD, SHOW, DELETE, END)


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
        # await update.callback_query.answer()
        await update.message.reply_text(text=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(
            "Hola! Soy tu asistente de recordatorios. ¿En qué puedo ayudarte hoy?"
        )
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return MENU


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose to add a parent or a child."""
    text = "Por favor, escribe el recordatorio que deseas agregar."
    buttons = [
        [
            InlineKeyboardButton(text="Recordatorio Periódico", callback_data=str(ADD_PERIODIC)),
            InlineKeyboardButton(text="Atrás", callback_data=str(END)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return ADD


async def add_periodic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose to add a parent or a child."""
    text = "Por favor, escribe el recordatorio que deseas agregar."
    await context.bot.send_message(update.effective_chat.id, text=text, parse_mode="markdown")

    return LISTENING_PERIODIC_REMINDER


async def show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Muestra los recordatorios."""
    text = "Aquí tienes tus recordatorios:"
    await context.bot.send_message(update.effective_chat.id, text=text, parse_mode="markdown")

    return SHOW

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Elimina los recordatorios."""
    text = "Por favor, selecciona el recordatorio que deseas eliminar."
    await context.bot.send_message(update.effective_chat.id, text=text, parse_mode="markdown")

    return DELETE


async def end_second_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to top level conversation."""
    context.user_data[START_OVER] = True
    await start(update, context)

    return END


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    await update.message.reply_text("Okay, bye.")

    return END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End conversation from InlineKeyboardButton."""
    await update.callback_query.answer()

    text = "See you around!"
    await update.callback_query.edit_message_text(text=text)

    return END

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    # await update.message.reply_text(update.message.text)
    # await context.bot.send_message(update.effective_chat.id, text=update.message.text, parse_mode="markdown")
    await update.message.reply_text(update.message.text)
    logger.info(update.message.text)
    
    context.user_data[START_OVER] = True
    await start(update, context)

    return END


# async def save_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
#     """Save input for feature and return to feature selection."""
#     user_data = context.user_data
#     user_data[FEATURES][user_data[CURRENT_FEATURE]] = update.message.text

#     user_data[START_OVER] = True

#     return await select_feature(update, context)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()
    
    
    add_handlers = [
        CallbackQueryHandler(add_periodic, pattern="^" + str(ADD_PERIODIC) + "$"),
        CallbackQueryHandler(echo, pattern="^" + str(LISTENING_REMINDER) + "$"),
    ]

    # Set up second level ConversationHandler (adding a person)
    second_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(add, pattern="^" + str(ADD) + "$")],
        states={
            ADD: add_handlers,
            LISTENING_PERIODIC_REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, echo)],
        },
        fallbacks=[
            CommandHandler("stop", stop),
            CallbackQueryHandler(end_second_level, pattern="^" + str(END) + "$"),
            # CallbackQueryHandler(add_periodic, pattern="^" + str(ADD_PERIODIC) + "$"),
            ],
        map_to_parent={
            END: MENU,
        },
    )

    # Set up top level ConversationHandler (selecting action)
    # Because the states of the third level conversation map to the ones of the second level
    # conversation, we need to make sure the top level conversation can also handle them
    selection_handlers = [
        second_level,
    ]
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: selection_handlers,  # type: ignore[dict-item]
            STOPPING: [CommandHandler("start", start)],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()