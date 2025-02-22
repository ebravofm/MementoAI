
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.delete import confirm_delete_all, confirm_delete_by_name
from handlers.show import show_all, show_by_name
from utils.misc import handle_audio_or_text
from handlers.add import add_reminder_timer
from utils.agents import process_prompt
from utils.logger import logger

from utils.constants import (
    START_OVER,
    START_WITH_NEW_REPLY,
    MESSAGE_TEXT,
    MENU,
    END,
    ADD,
    SHOW,
    DELETE
)

from texts.texts import (
    TXT_HELP,
    TXT_ERROR,
    TXT_WELCOME,
    TXT_WELCOME_2,
    TXT_BUTTON_NEW_REMINDER,
    TXT_BUTTON_LIST_REMINDERS,
    TXT_BUTTON_DELETE_REMINDERS,
    TXT_STOP,
    TXT_PROCESSING
)

from handlers.misc import send_message




# Top level conversation callbacks
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Selecciona una acción: Agregar recordatorio, mostrar recordatorios o eliminar recordatorios."""
    
    full_text = TXT_WELCOME
    text_then = TXT_WELCOME_2
    buttons = [
        [
            InlineKeyboardButton(text=TXT_BUTTON_NEW_REMINDER, callback_data=str(ADD)),
        ],
        [
            InlineKeyboardButton(text=TXT_BUTTON_LIST_REMINDERS, callback_data=str(SHOW)),
            InlineKeyboardButton(text=TXT_BUTTON_DELETE_REMINDERS, callback_data=str(DELETE)),
        ],    
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    logger.info(context.user_data)
    if context.user_data.get(START_OVER):
        if context.user_data.get(START_WITH_NEW_REPLY):
            await send_message(update, context, text=text_then, keyboard=keyboard)
        else:
            await send_message(update, context, text=text_then, keyboard=keyboard)
    else:
        logger.info('test1')
        await send_message(update, context, text=full_text, keyboard=keyboard)
        
    context.user_data[START_OVER] = False
    context.user_data[START_WITH_NEW_REPLY] = False
    context.user_data[MESSAGE_TEXT] = None
    return MENU


async def end_second_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[START_OVER] = True
    await start(update, context)
    return MENU


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(TXT_STOP)
    return END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    text = "See you around!"
    await update.callback_query.edit_message_text(text=text)
    return END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    await send_message(update, context, text=TXT_ERROR)
    
    # Limpiar el estado y volver al menú principal
    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True
    context.user_data[MESSAGE_TEXT] = None
    
    await start(update, context)
    
    return MENU
    
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = TXT_HELP
    
    await send_message(update, context, text=help_text)
    
    await start(update, context)
    
    return MENU

    
async def crossroad(update, context, response):

    if response["category"] == "add_reminder":
        await add_reminder_timer(update, context)
                        
    elif response["category"] == "show":
        if response["all_reminders"]:
            await show_all(update, context)
        else:
            await show_by_name(update, context, name=response["reminder_name"])

    elif response["category"] == "delete":
        if response["all_reminders"]:
            await confirm_delete_all(update, context)
        else:
            await confirm_delete_by_name(update, context)
                     
                     

async def categorize_and_reply(update, context):
    """Categorizes a prompt into three categories."""
    
    await send_message(update, context, text=TXT_PROCESSING)
    
    await handle_audio_or_text(update, context)
    query = context.user_data.get(MESSAGE_TEXT)

    response = process_prompt(update, context, query)
    
    logger.info(f"Response: {response}")
    
    await crossroad(update, context, response)

