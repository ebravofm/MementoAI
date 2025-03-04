from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from functions.jobs import filter_jobs
from utils.logger import logger
from utils.constants import (
    DELETE,
    DELETE_ALL,
    DELETE_BY_NAME,
    END,
    CONFIRM_DELETE_ALL,
    CONFIRMED_DELETE_ALL,
    MENU,
    BACK,
    LISTENING_TO_DELETE_BY_NAME
)

from texts.texts import (
    TXT_DELETE,
    TXT_BUTTON_BACK,
    TXT_DELETE_ALL,
    TXT_DELETE_BY_NAME,
    TXT_BUTTON_CANCEL,
    TXT_BUTTON_CONTINUE,
    TXT_CONFIRM_DELETE_ALL,
    TXT_NO_REMINDERS_TO_DELETE,
    TXT_ALL_REMINDERS_DELETED,
    TXT_NO_REMINDER_FOUND,
    TXT_REMINDER_DELETED,
    TXT_BUTTON_CONFIRM,
    TXT_LISTENING_TO_DELETE_BY_NAME
)

from handlers.misc import send_message, continue_keyboard, hide_keyboard



async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = TXT_DELETE
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text=TXT_DELETE_ALL, callback_data=str(DELETE_ALL)),
            InlineKeyboardButton(text=TXT_DELETE_BY_NAME, callback_data=str(DELETE_BY_NAME)),
        ],
        [
            InlineKeyboardButton(text=TXT_BUTTON_BACK, callback_data=str(BACK)),
        ],
    ])
    await send_message(update, context, text=text, keyboard=keyboard, edit=True)
    return DELETE


async def confirm_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = TXT_CONFIRM_DELETE_ALL
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text=TXT_BUTTON_CONFIRM, callback_data=str(CONFIRMED_DELETE_ALL)),
            InlineKeyboardButton(text=TXT_BUTTON_CANCEL, callback_data=str(END)),
        ]
    ])
    await send_message(update, context, text=text, keyboard=keyboard, edit=True)
        
    return CONFIRM_DELETE_ALL
    

async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Eliminar todos los recordatorios."""
    logger.info("Eliminando todos los recordatorios.")
    jobs = filter_jobs(context.job_queue, start_date=None, end_date=None, chat_id=update.effective_chat.id, job_type=None)

    if not jobs:
        text = TXT_NO_REMINDERS_TO_DELETE

        msg = await send_message(update, context, text=text, keyboard=continue_keyboard, edit=True)
        
    else:
        for job in jobs:
            job.schedule_removal()   
            
        text = TXT_ALL_REMINDERS_DELETED
        msg = await send_message(update, context, text=text, edit=True, keyboard=continue_keyboard)
        
    await hide_keyboard(update, context, msg=msg)
    

async def listening_to_delete_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text=TXT_BUTTON_CANCEL, callback_data=str(END))]
    ])
    
    await send_message(update, context, text=TXT_LISTENING_TO_DELETE_BY_NAME, keyboard=keyboard, edit=True)
    
    return LISTENING_TO_DELETE_BY_NAME    



async def delete_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Delete reminders by name."""
    job_name = context.user_data['JOB_TO_DELETE']

    context.user_data['JOB_TO_DELETE'] = None
    jobs = filter_jobs(context.job_queue, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type=None, job_name=job_name)
    if not jobs:
        msg = await send_message(update, context, text=TXT_NO_REMINDER_FOUND.format(name=job_name), keyboard=continue_keyboard, edit=True)
        
    else:

        for job in jobs:
            job.schedule_removal()
            
        msg = await send_message(update, context, text=TXT_REMINDER_DELETED.format(name=job_name), edit=True, keyboard=continue_keyboard)
        
    await hide_keyboard(update, context, msg=msg)