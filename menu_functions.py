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

from telegram.ext import ContextTypes
from telegram import Update
from telegram.constants import ChatAction
from datetime import datetime, timedelta
from handlers.jobs import filter_jobs
from handlers.categorize import process_prompt, select_job_by_name
from handlers.set_reminders import set_reminder_timer
from handlers.notifications import delete_all_confirmation, delete_reminder_confirmation
from utils.transcriptions import audio_handling


from handlers.set_reminders import alarm, alarm_minus_30
from handlers.jobs import remove_job_if_exists
from utils.agents import reminder_from_prompt, reminder_to_text, model
from utils.logger import logger, tz
from collections import defaultdict
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
    LISTENING_TO_SHOW_BY_NAME,
    DELETE_ALL,
    DELETE_BY_NAME,
    LISTENING_TO_DELETE_BY_NAME,
    CONFIRM_DELETE_ALL,
    CONFIRMED_DELETE_ALL,
    CONFIRM_DELETE_BY_NAME,
    CONFIRMED_DELETE_BY_NAME,
    START_OVER,
    START_WITH_NEW_REPLY,
    STOPPING,
    END
)

from datetime import datetime, timedelta

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
        ],
        [
            InlineKeyboardButton(text="Mostrar recordatorios", callback_data=str(SHOW)),
            InlineKeyboardButton(text="Eliminar recordatorios", callback_data=str(DELETE)),
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

    return MENU


async def add_reminder_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.message.text
    chat_id = update.effective_chat.id
    # Generate reminder from the text
    reminder = reminder_from_prompt(query)
    reminder['chat_id'] = chat_id

    logger.info(f"Reminder: {reminder}")

    # Convert the reminder time to a localized datetime object
    timer_date = reminder['Time'].replace(tzinfo=None)
    timer_date = tz.localize(timer_date)
    timer_date_string = timer_date.strftime("%H:%M %d/%m/%Y")

    timer_name = f"{reminder['Title']} ({timer_date_string})"
    reminder['text'] = reminder_to_text(reminder)

    try:
        # Calculate the time remaining in seconds
        now = datetime.now(tz)
        seconds_until_due = (timer_date - now).total_seconds()

        # Check if the time is in the past
        if seconds_until_due <= 0:
            await update.effective_message.reply_text("No es posible programar recordatorios en el pasado.")
            return

        # Remove existing jobs with the same name and add the new one
        job_removed = remove_job_if_exists(timer_name, context)
        reminder['type'] = 'parent'
        
        context.job_queue.run_once(
            alarm,
            when=timer_date,
            chat_id=chat_id,
            name=timer_name,
            data=reminder,
        )
        
        reminder['type'] = '-30'
        context.job_queue.run_once(
            alarm_minus_30,
            when=timer_date - timedelta(minutes=30),
            chat_id=chat_id,
            name=timer_name,
            data=reminder,
        )


        # Confirmation message
        await update.effective_message.reply_text('Se agendó el siguiente recordatorio:', parse_mode="markdown")
        await update.effective_message.reply_text(reminder['text'], parse_mode="markdown")
        
        context.user_data[START_OVER] = True
        context.user_data[START_WITH_NEW_REPLY] = True

        await start(update, context)

    except (IndexError, ValueError) as e:
        await update.effective_message.reply_text(f"An error occurred: {str(e)}")
        
    return MENU


async def show_all(update, context, start_date: datetime = None, end_date: datetime = None, header="Recordatorios Programados"):
    """Lists all scheduled jobs in the JobQueue grouped by day."""
    # Filtrar trabajos usando la función filter_jobs
    chat_id = update.effective_chat.id
    jobs = filter_jobs(context, start_date=start_date, end_date=end_date, chat_id=chat_id, job_type='parent')

    if not jobs:
        try:
            await update.callback_query.edit_message_text("No hay recordatorios programados.")
        except AttributeError:
            await update.effective_message.reply_text("No hay recordatorios programados.")
            
        context.user_data[START_OVER] = True
        context.user_data[START_WITH_NEW_REPLY] = True

        await start(update, context)

        return MENU

    # Agrupar trabajos por día
    jobs_by_day = defaultdict(list)
    for job in jobs:
        if job.data and "Time" in job.data and "Title" in job.data:
            job_day = job.next_run_time.date()
            jobs_by_day[job_day].append(job)

    # Formatear la lista de trabajos por día
    message = f"*{header}:*\n"
    for day, jobs in sorted(jobs_by_day.items()):
        day_str = day.strftime("%A %d %B")  # Ejemplo: Tuesday 23 January 2025
        message += f"\n*{day_str}*:\n"
        message += "\n".join(
            [f"  - {job.data['Time'].strftime('%H:%M')}: {job.data['Title']}" for job in jobs]
        )
        message += "\n"

    # Enviar el mensaje al usuario
    try:
        await update.callback_query.edit_message_text(message, parse_mode="markdown")
    except AttributeError:
        await update.effective_message.reply_text(message, parse_mode="markdown")
        
    logger.info(context.user_data)
    logger.info(context.chat_data)

        
    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True

    await start(update, context)
    
    return MENU


async def show_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show today's reminders."""
    today = datetime.now()
    await show_all(update, context, start_date=today, end_date=today, header="Recordatorios Programados para Hoy")
    
    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True

    await start(update, context)
    
    return MENU


async def show_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show tomorrow's reminders."""
    tomorrow = datetime.now() + timedelta(days=1)
    await show_all(update, context, start_date=tomorrow, end_date=tomorrow, header="Recordatorios Programados para Mañana")
    
    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True
    
    await start(update, context)
    
    return MENU

async def show_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show reminders for the next 7 days."""
    today = datetime.now()
    await show_all(update, context, start_date=today, end_date=today + timedelta(days=7), header="Recordatorios Programados para la Semana")
    
    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True
    
    await start(update, context)
    
    return MENU 


async def show_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show reminder by name."""
    name = select_job_by_name(update, context, update.effective_message.text)
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type='parent', name=name)
    if not jobs:
        await update.message.reply_text(f"No se encontró el recordatorio '{name}'.")
        
        context.user_data[START_OVER] = True
        context.user_data[START_WITH_NEW_REPLY] = True
        
        await start(update, context)
        return MENU

    job = jobs[0]
    
    await update.effective_message.reply_text(job.data['text'], parse_mode="markdown")
    
    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True
    
    await start(update, context)
    
    return MENU


    

async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Delete all reminders."""
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_chat.id, name=None, job_type=None)

    if not jobs:
        try:
            await update.callback_query.edit_message_text("No se encontraron trabajos para eliminar.")
        except:
            await update.effective_message.reply_text("No se encontraron trabajos para eliminar.")
        
        context.user_data[START_OVER] = True
        context.user_data[START_WITH_NEW_REPLY] = True
        
        await start(update, context)
        return MENU

    for job in jobs:
        job.schedule_removal()   
        
    text = "Todos los recordatorios han sido eliminados."
    try:
        await update.callback_query.edit_message_text(text=text, parse_mode="markdown")
    except AttributeError:
        await update.effective_message.reply_text(text=text, parse_mode="markdown")
        
    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True

    await start(update, context)
    return MENU


async def show_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show reminder by name."""
    name = select_job_by_name(update, context, update.effective_message.text)
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type='parent', name=name)
    if not jobs:
        await update.effective_message.reply_text(f"No se encontró el recordatorio '{name}'.")
        
        context.user_data[START_OVER] = True
        context.user_data[START_WITH_NEW_REPLY] = True
        
        await start(update, context)
        return MENU

    job = jobs[0]
    
    await update.effective_message.reply_text(job.data['text'], parse_mode="markdown")
    
    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True
    
    await start(update, context)
    
    return MENU


async def delete_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Delete reminders by name."""
    name = context.user_data['JOB_TO_DELETE']
    logger.info(f"Deleting job: {name}")
    context.user_data['JOB_TO_DELETE'] = None
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type=None, name=name)
    if not jobs:
        await update.message.reply_text(f"No se encontró el recordatorio '{name}'.")
        
        context.user_data[START_OVER] = True
        context.user_data[START_WITH_NEW_REPLY] = True
        
        await start(update, context)
        return MENU

    for job in jobs:
        job.schedule_removal()
        
    try:
        await update.callback_query.edit_message_text(f"El recordatorio '{name}' ha sido eliminado.")
    except AttributeError:
        await update.effective_message.reply_text(f"El recordatorio '{name}' ha sido eliminado.")
    
    context.user_data[START_OVER] = True
    context.user_data[START_WITH_NEW_REPLY] = True
    
    await start(update, context)
    
    return MENU


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
    
    await crossroad(update, context, response)


async def crossroad(update, context, response):

    if response["category"] == "add_reminder":
        if response["is_periodic"]:
            await update.message.reply_text("El prompt indica agregar un recordatorio periódico.")
        else:
            await add_reminder_timer(update, context)
            
            
    elif response["category"] == "show":
        if response["all_reminders"]:
            await show_all(update, context)
        else:
            await show_by_name(update, context)
            
            
    elif response["category"] == "delete":
        if response["all_reminders"]:
            await confirm_delete_all(update, context)
        else:
            await delete_reminder_confirmation(update, context, response["reminder_name"])

