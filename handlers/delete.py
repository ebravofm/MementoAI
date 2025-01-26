from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils.misc import cleanup_and_restart, handle_audio_or_text
from utils.agents import select_job_by_name
from functions.jobs import filter_jobs
from utils.logger import logger
from commands import start
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
    MESSAGE_TEXT   
)


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


async def confirm_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "❌ *Eliminar todos los recordatorios* ❌\n\n¿Estás seguro de que deseas eliminar todos los recordatorios? Esta acción es irreversible."
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data=str(CONFIRMED_DELETE_ALL)),
            InlineKeyboardButton(text="❌ Cancelar", callback_data=str(END)),
        ]
    ])
    try:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="markdown")
    except AttributeError:
        await update.effective_message.reply_text(text=text, reply_markup=keyboard, parse_mode="markdown")
        
    return CONFIRM_DELETE_ALL
    

@cleanup_and_restart
async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Eliminar todos los recordatorios."""
    logger.info("Eliminando todos los recordatorios.")
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_chat.id, name=None, job_type=None)

    if not jobs:
        text = "ℹ️ *No se encontraron recordatorios para eliminar* ℹ️"
        try:
            await update.callback_query.edit_message_text(text=text, parse_mode="markdown")
        except AttributeError:
            await update.effective_message.reply_text(text=text, parse_mode="markdown")
        
        return 

    for job in jobs:
        job.schedule_removal()   
        
    text = "🗑️ *Todos los recordatorios han sido eliminados* 🗑️"
    try:
        await update.callback_query.edit_message_text(text=text, parse_mode="markdown")
    except AttributeError:
        await update.effective_message.reply_text(text=text, parse_mode="markdown")


async def confirm_delete_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    
    await handle_audio_or_text(update, context)
    query = context.user_data.get(MESSAGE_TEXT)
    
    name = select_job_by_name(update, context, query)
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type=None, name=name)
    if not jobs:
        text = f"ℹ️ *No se encontró el recordatorio '{name}'* ℹ️"
        await update.message.reply_text(text=text, parse_mode="markdown")
        
        context.user_data[START_OVER] = True
        context.user_data[START_WITH_NEW_REPLY] = True
        
        await start(update, context)
        return MENU
    
    context.user_data['JOB_TO_DELETE'] = jobs[0].name

    text = f"❌ *Eliminar recordatorio* ❌\n\n¿Estás seguro de que deseas eliminar el siguiente recordatorio?\n\n{jobs[0].data['text']}"
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data=str(CONFIRMED_DELETE_BY_NAME)),
            InlineKeyboardButton(text="🚫 Cancelar", callback_data=str(END)),
        ]
    ])
    await update.effective_message.reply_text(text=text, reply_markup=keyboard, parse_mode="markdown")
    
    return CONFIRM_DELETE_BY_NAME


@cleanup_and_restart
async def delete_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Delete reminders by name."""
    name = context.user_data['JOB_TO_DELETE']
    logger.info(f"Deleting job: {name}")
    context.user_data['JOB_TO_DELETE'] = None
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type=None, name=name)
    if not jobs:
        await update.message.reply_text(f"No se encontró el recordatorio '{name}'.")
        
        return

    for job in jobs:
        job.schedule_removal()
        
    try:
        await update.callback_query.edit_message_text(f"El recordatorio *{name}* ha sido eliminado.", parse_mode="markdown")
    except AttributeError:
        await update.effective_message.reply_text(f"El recordatorio *{name}* ha sido eliminado.", parse_mode="markdown")