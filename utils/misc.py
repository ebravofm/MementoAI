from telegram.ext import ContextTypes
from telegram import Update

from utils.transcriptions import audio_handling
from commands import start
from utils.logger import logger
from utils.constants import (
    START_OVER,
    START_WITH_NEW_REPLY,
    MESSAGE_TEXT,
    MENU
)

from functools import wraps


def cleanup_and_restart(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        result = await func(update, context, *args, **kwargs)
        
        context.user_data[START_OVER] = True
        context.user_data[START_WITH_NEW_REPLY] = True
        context.user_data[MESSAGE_TEXT] = None
        
        await start(update, context)
        return MENU
        
    return wrapper


async def handle_audio_or_text(update, context):
    """Handle audio or text messages."""
    
    if not context.user_data.get(MESSAGE_TEXT):
        if update.message.voice:
            logger.info("Audio message received.")
            query = await audio_handling(update, context)  # Convert audio to text

        else:
            logger.info("Message received.")
            query = update.message.text

        context.user_data[MESSAGE_TEXT] = query
        logger.info('Test2: ' + context.user_data[MESSAGE_TEXT])
        
        
def reminder_to_text(reminder, header = "📆 *Recordatorio*📆\n") -> str:
    
    reminder['Time_String'] = reminder['Time'].strftime("%H:%M %d/%m/%Y")
    
    text = header
    if reminder['Title']:
        text += f"\n*Evento*: {reminder['Title']}"
    if reminder['Time']:
        text += f"\n*Fecha*: {reminder['Time_String']}"
    if reminder['Location']:
        text += f"\n*Ubicación*: {reminder['Location']}"
    if reminder['Details']:
        text += f"\n*Detalle*: {reminder['Details']}"
    
    return text

        
