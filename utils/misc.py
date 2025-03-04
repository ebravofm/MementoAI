from telegram.ext import ContextTypes
from telegram import Update

from utils.transcriptions import audio_handling
# from commands import start
from utils.logger import logger
from utils.constants import (
    START_OVER,
    START_WITH_NEW_REPLY,
    MESSAGE_TEXT,
    MENU
)

from functools import wraps

from texts.texts import ( 
    TXT_REMINDER_TITLE,
    TXT_REMINDER_TIME,
    TXT_REMINDER_LOCATION,
    TXT_REMINDER_DETAILS,
    TXT_REMINDER_DAYS,
    TXT_PERIODIC_REMINDER_TITLE                         
)


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
        

       
def reminder_to_text(reminder, header = "📆 *Recordatorio*📆\n") -> str:
    
    if reminder['run'] == 'once':
        reminder['Time_String'] = reminder['Time'].strftime("%H:%M %d/%m/%Y")
        
        text = header
        if reminder['Title']:
            # text += f"\n*Evento*: {reminder['Title']}"
            text += TXT_REMINDER_TITLE.format(TITLE=reminder['Title'])
        if reminder['Time']:
            # text += f"\n*Fecha*: {reminder['Time_String']}"
            text += TXT_REMINDER_TIME.format(TIME=reminder['Time_String'])
        if reminder['Location']:
            # text += f"\n*Ubicación*: {reminder['Location']}"
            text += TXT_REMINDER_LOCATION.format(LOCATION=reminder['Location'])
        if reminder['Details']:
            # text += f"\n*Detalle*: {reminder['Details']}"
            text += TXT_REMINDER_DETAILS.format(DETAILS=reminder['Details'])
        
    elif reminder['run'] == 'periodic':
        reminder['Time_String'] = reminder['Time'].strftime("%H:%M")
        days_of_week = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
        text = header
        if reminder['Title']:
            # text += f"\n*Evento*: {reminder['Title']} (Periódico)"
            text += TXT_PERIODIC_REMINDER_TITLE.format(TITLE=reminder['Title'])
        if reminder['Days']:
            # text += f"\n*Días*:"
            # text += ", ".join(days_of_week[day] for day in reminder['Days']) if len(reminder['Days']) < 7 else "Todos los días"
            days = ", ".join(days_of_week[day] for day in reminder['Days']) if len(reminder['Days']) < 7 else "Todos los días"
            text += TXT_REMINDER_DAYS.format(DAYS=days)
        if reminder['Time']:
            # text += f"\n*Hora*: {reminder['Time_String']}"
            text += TXT_REMINDER_TIME.format(TIME=reminder['Time_String'])
        if reminder['Details']:
            # text += f"\n*Detalles*: {reminder['Details']}"
            text += TXT_REMINDER_DETAILS.format(DETAILS=reminder['Details'])
        
    return text            
