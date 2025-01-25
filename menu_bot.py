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

from menu_dummy_functions import echo, start, show_all, show_today, show_tomorrow, show_week, show_by_name

from utils.logger import logger
from config import TG_TOKEN

TOKEN = TG_TOKEN

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# State definitions for top level conversation


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose to add a parent or a child."""
    text = "Por favor, escribe el recordatorio que deseas agregar. Si quieres agregar un recordatorio periódico, selecciona la opción correspondiente."
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
    await update.callback_query.edit_message_text(text=text, parse_mode="markdown")
    # await context.bot.send_message(update.effective_chat.id, text=text, parse_mode="markdown")

    return LISTENING_PERIODIC_REMINDER


async def show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose to add a parent or a child."""
    text = "Por favor, selecciona la opción que deseas."
    buttons = [
        [
            InlineKeyboardButton(text="Ver todos los recordatorios", callback_data=str(SHOW_ALL)),
            InlineKeyboardButton(text="Ver recordatorio específico", callback_data=str(SHOW_BY_NAME)),
        ],
        [
            InlineKeyboardButton(text="Ver todos los recordatorios de hoy", callback_data=str(SHOW_TODAY)),
            InlineKeyboardButton(text="Ver todos los recordatorios de mañana", callback_data=str(SHOW_TOMORROW)),
        ],
        [
            InlineKeyboardButton(text="Ver todos los recordatorios de los próximos 7 días", callback_data=str(SHOW_WEEK)),
        ],
        [
            InlineKeyboardButton(text="Atrás", callback_data=str(END)),
        ],
    ]

    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

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
        MessageHandler(filters.TEXT & ~filters.COMMAND, echo),
    ]
    
    show_handlers = [
        CallbackQueryHandler(show_all, pattern="^" + str(SHOW_ALL) + "$"),
        CallbackQueryHandler(show_today, pattern="^" + str(SHOW_TODAY) + "$"),
        CallbackQueryHandler(show_tomorrow, pattern="^" + str(SHOW_TOMORROW) + "$"),
        CallbackQueryHandler(show_week, pattern="^" + str(SHOW_WEEK) + "$"),
        CallbackQueryHandler(show_by_name, pattern="^" + str(SHOW_BY_NAME) + "$"),
    ]

    ### Set up second level ConversationHandler (adding a person)
    second_level_add = ConversationHandler(
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

    second_level_show = ConversationHandler(
        entry_points=[CallbackQueryHandler(show, pattern="^" + str(SHOW) + "$")],
        states={
            SHOW: show_handlers,
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
    
    second_level_delete = ConversationHandler(
        entry_points=[CallbackQueryHandler(delete, pattern="^" + str(DELETE) + "$")],
        states={
            DELETE: delete_handlers,
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
        second_level_add,
        second_level_show,
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