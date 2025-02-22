from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils.misc import handle_audio_or_text
from utils.agents import select_job_by_name
from functions.jobs import filter_jobs
from utils.logger import logger
from utils.constants import (
    DELETE,
    DELETE_ALL,
    DELETE_BY_NAME,
    END,
    LISTENING_TO_DELETE_BY_NAME,
    CONFIRM_DELETE_ALL,
    CONFIRMED_DELETE_ALL,
    CONFIRM_DELETE_BY_NAME,
    CONFIRMED_DELETE_BY_NAME,
    START_OVER,
    START_WITH_NEW_REPLY,
    MESSAGE_TEXT,
    MENU
)

from texts.texts import (
    TXT_DELETE,
    TXT_BUTTON_BACK,
    TXT_DELETE_ALL,
    TXT_DELETE_BY_NAME,
    TXT_LISTENING_TO_DELETE_BY_NAME,
    TXT_BUTTON_CANCEL,
    TXT_BUTTON_CONTINUE,
    TXT_CONFIRM_DELETE_ALL,
    TXT_NO_REMINDERS_TO_DELETE,
    TXT_ALL_REMINDERS_DELETED,
    TXT_NO_REMINDER_FOUND,
    TXT_CONFIRM_DELETE_BY_NAME,
    TXT_REMINDER_DELETED,
    TXT_BUTTON_CONFIRM,
)

from handlers.misc import send_message



async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = TXT_DELETE
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text=TXT_DELETE_ALL, callback_data=str(DELETE_ALL)),
            InlineKeyboardButton(text=TXT_DELETE_BY_NAME, callback_data=str(DELETE_BY_NAME)),
        ],
        [
            InlineKeyboardButton(text=TXT_BUTTON_BACK, callback_data=str(END)),
        ],
    ])
    await send_message(update, context, text=text, keyboard=keyboard, edit=True)
    return DELETE


async def listening_to_delete_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = TXT_LISTENING_TO_DELETE_BY_NAME
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text=TXT_BUTTON_CANCEL, callback_data=str(END))]
    ])
    await send_message(update, context, text=text, keyboard=keyboard, edit=True)
    return LISTENING_TO_DELETE_BY_NAME    


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
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_chat.id, name=None, job_type=None)

    if not jobs:
        text = TXT_NO_REMINDERS_TO_DELETE
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=TXT_BUTTON_CONTINUE, callback_data=str(MENU))]
        ])

        await send_message(update, context, text=text, keyboard=keyboard, edit=True)
        
        return MENU

    for job in jobs:
        job.schedule_removal()   
        
    text = TXT_ALL_REMINDERS_DELETED
    await send_message(update, context, text=text, edit=True)


async def confirm_delete_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    
    await handle_audio_or_text(update, context)
    query = context.user_data.get(MESSAGE_TEXT)
    
    name = select_job_by_name(update, context, query)
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type=None, name=name)
    if not jobs:
        text = TXT_NO_REMINDER_FOUND.format(name=name)
        # await update.message.reply_text(text=text, parse_mode="markdown")
        await send_message(update, context, text=text)
        
        context.user_data[START_OVER] = True
        context.user_data[START_WITH_NEW_REPLY] = True
        
        return MENU
    
    context.user_data['JOB_TO_DELETE'] = jobs[0].name

    text = TXT_CONFIRM_DELETE_BY_NAME + f"\n\n{jobs[0].data['text']}"
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text=TXT_BUTTON_CONFIRM, callback_data=str(CONFIRMED_DELETE_BY_NAME)),
            InlineKeyboardButton(text=TXT_BUTTON_CANCEL, callback_data=str(END)),
        ]
    ])
    # await update.effective_message.reply_text(text=text, reply_markup=keyboard, parse_mode="markdown")
    await send_message(update, context, text=text, keyboard=keyboard)
    
    return CONFIRM_DELETE_BY_NAME


async def delete_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Delete reminders by name."""
    name = context.user_data['JOB_TO_DELETE']
    logger.info(f"Deleting job: {name}")
    context.user_data['JOB_TO_DELETE'] = None
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type=None, name=name)
    if not jobs:
        # await update.message.reply_text(TXT_NO_REMINDER_FOUND.format(name=name))
        await send_message(update, context, text=TXT_NO_REMINDER_FOUND.format(name=name))
        
        return

    for job in jobs:
        job.schedule_removal()
        
    # try:
    #     await update.callback_query.edit_message_text(TXT_REMINDER_DELETED.format(name=name), parse_mode="markdown")
    # except AttributeError:
    #     await update.effective_message.reply_text(TXT_REMINDER_DELETED.format(name=name), parse_mode="markdown")
    await send_message(update, context, text=TXT_REMINDER_DELETED.format(name=name))