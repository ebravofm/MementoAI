from telegram.ext import ContextTypes
from telegram import Update
from telegram.constants import ChatAction
from datetime import datetime, timedelta
from handlers.jobs import list_jobs
from handlers.categorize import process_prompt
from handlers.set_reminders import set_reminder_timer
from handlers.notifications import show_reminder, delete_all_confirmation, delete_reminder_confirmation
from utils.transcriptions import audio_handling

from utils.logger import logger


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text("""¡Hola! Aquí tienes los comandos disponibles para interactuar con el bot:

*Comandos básicos:*
- **`/start`**: Inicia el bot y muestra un mensaje de bienvenida.
- **`/help`**: Muestra esta lista de comandos y su descripción.

*Gestión de recordatorios:*
- **`/list`**: Muestra todos los trabajos (tareas) programados en el sistema.
- **`/list_day`**: Muestra las tareas programadas para hoy.
- **`/list_next_day`**: Muestra las tareas programadas para el día siguiente.
- **`/list_week`**: Muestra las tareas pendientes para el resto de la semana, desde el día actual hasta el domingo.
- **`/list_next_week`**: Muestra las tareas programadas para la próxima semana completa (de lunes a domingo).

*Creación de recordatorios:*
- Puedes crear recordatorios enviando un mensaje de texto o un mensaje de voz. El bot procesará la información y programará un recordatorio según el contenido proporcionado.

*Notificaciones automáticas:*
- Cada día, a las 11:00 PM, recibirás una notificación con las tareas programadas para el día siguiente.""", parse_mode="markdown")
    

async def categorize_and_reply(update, context):
    """Categorizes a prompt into three categories."""
    

    await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

    # Determine the message type (audio or text)
    if update.message.voice:  # Audio message
        logger.info("Audio message received.")
        query = await audio_handling(update, context)  # Convert audio to text
    else:  # Text message
        logger.info("Message received.")
        query = update.message.text

    
    # use procees_prompt function from categorize.py
    response = process_prompt(update, context, query)
    logger.info(f"Response: {response}")


    if response["category"] == "add_reminder":
        if response["is_periodic"]:
            await update.message.reply_text("El prompt indica agregar un recordatorio periódico.")
        else:
            await set_reminder_timer(update, context, query)
            
            
    elif response["category"] == "show":
        if response["all_reminders"]:
            await list_jobs(update, context, start_date=None, end_date=None, header="Recordatorios Programados")
        else:
            await show_reminder(update, context, response["reminder_name"])
            
            
    elif response["category"] == "delete":
        if response["all_reminders"]:
            await delete_all_confirmation(update, context)
        else:
            await delete_reminder_confirmation(update, context, response["reminder_name"])



async def list_jobs_for_current_day(update, context):
    """Lists all scheduled jobs for the current day."""
    await list_jobs(update, context, start_date=datetime.now(), end_date=datetime.now(), header="Recordatorios Programados para Hoy")
    # await list_jobs_for_day(update, context, datetime.now())


async def list_jobs_for_next_day(update, context):
    """Lists all scheduled jobs for the next day."""
    next_day = datetime.now() + timedelta(days=1)
    await list_jobs(update, context, start_date=next_day, end_date=next_day, header="Recordatorios Programados para Mañana")
    # await list_jobs_for_day(update, context, next_day)


async def list_jobs_for_current_week(update, context):
    """Lists all scheduled jobs for the current week."""
    today = datetime.now()
    await list_jobs(update, context, start_date=today, end_date=today + timedelta(days=7), header="Recordatorios Programados para la Semana")
    # await list_jobs_for_week(update, context)

