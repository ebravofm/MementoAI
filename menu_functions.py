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
    MESSAGE_TEXT,
    END
)

from datetime import datetime, timedelta
from functools import wraps
import locale
locale.setlocale(locale.LC_TIME, "es_ES")


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


# Top level conversation callbacks
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Selecciona una acción: Agregar recordatorio, mostrar recordatorios o eliminar recordatorios."""
    
    full_text = "🤖 *Bienvenid@ a MementoAI* 🤖\n\nEstoy aquí para ayudarte a gestionar tus recordatorios de manera fácil y eficiente.\n\n¿En qué puedo ayudarte?"
    text_then = "¿En qué más puedo ayudarte?"
    buttons = [
        [
            InlineKeyboardButton(text="📝 Agregar nuevo recordatorio", callback_data=str(ADD)),
        ],
        [
            InlineKeyboardButton(text="📄 Ver recordatorios", callback_data=str(SHOW)),
            InlineKeyboardButton(text="❌ Eliminar recordatorios", callback_data=str(DELETE)),
        ],    
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    logger.info(context.user_data)
    if context.user_data.get(START_OVER):
        if context.user_data.get(START_WITH_NEW_REPLY):
            await context.bot.send_message(update.effective_chat.id, text=text_then, reply_markup=keyboard, parse_mode="markdown")
        else:
            try:
                await update.callback_query.edit_message_text(text=text_then, reply_markup=keyboard, parse_mode="markdown")
            except AttributeError:
                await context.bot.send_message(update.effective_chat.id, text=text_then, reply_markup=keyboard, parse_mode="markdown")
    else:
        logger.info('test1')
        await update.effective_message.reply_text(text=full_text, reply_markup=keyboard, parse_mode="markdown")
        # await context.bot.send_message(update.effective_chat.id, text=full_text, reply_markup=keyboard, parse_mode="markdown")

    context.user_data[START_OVER] = False
    context.user_data[START_WITH_NEW_REPLY] = False
    context.user_data[MESSAGE_TEXT] = None
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


@cleanup_and_restart
async def add_reminder_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    await handle_audio_or_text(update, context)
    query = context.user_data.get('MESSAGE_TEXT')

    logger.info(f"Test: {query}")

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
        

    except (IndexError, ValueError) as e:
        await update.effective_message.reply_text(f"An error occurred: {str(e)}")
                
    return MENU


@cleanup_and_restart
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

        return

    # Agrupar trabajos por día
    jobs_by_day = defaultdict(list)
    for job in jobs:
        if job.data and "Time" in job.data and "Title" in job.data:
            job_day = job.next_run_time.date()
            jobs_by_day[job_day].append(job)

    # Formatear la lista de trabajos por día
    message = f"📅 *{header}* 📅:\n"
    for day, jobs in sorted(jobs_by_day.items()):
        day_str = day.strftime("%A %d/%B") 
        day_str = day_str.title()
        message += f"\n*{day_str}*:\n"
        message += "\n".join(
            [f"    {job.data['Time'].strftime('%H:%M')}: {job.data['Title']}" for job in jobs]
        )
        message += "\n"

    # Enviar el mensaje al usuario
    try:
        await update.callback_query.edit_message_text(message, parse_mode="markdown")
    except AttributeError:
        await update.effective_message.reply_text(message, parse_mode="markdown")
        

async def show_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show today's reminders."""
    today = datetime.now()
    await show_all(update, context, start_date=today, end_date=today, header="Recordatorios Programados para Hoy")
    return MENU
    
    
async def show_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show tomorrow's reminders."""
    tomorrow = datetime.now() + timedelta(days=1)
    await show_all(update, context, start_date=tomorrow, end_date=tomorrow, header="Recordatorios Programados para Mañana")
    return MENU


async def show_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show reminders for the next 7 days."""
    today = datetime.now()
    await show_all(update, context, start_date=today, end_date=today + timedelta(days=7), header="Recordatorios Programados para la Semana")
    return MENU


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

@cleanup_and_restart
async def show_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE, name=None) -> str:
    """Show reminder by name."""
    await handle_audio_or_text(update, context)
    query = context.user_data.get('MESSAGE_TEXT')
    
    if not name:
        name = select_job_by_name(update, context, query)
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type='parent', name=name)
    if not jobs:
        await update.effective_message.reply_text(f"No se encontró el recordatorio '{name}'.")
        
        return

    job = jobs[0]
    
    await update.effective_message.reply_text(job.data['text'], parse_mode="markdown")


async def confirm_delete_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    
    await handle_audio_or_text(update, context)
    query = context.user_data.get('MESSAGE_TEXT')
    
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


async def categorize_and_reply(update, context):
    """Categorizes a prompt into three categories."""
    
    await handle_audio_or_text(update, context)
    query = context.user_data.get('MESSAGE_TEXT')

    response = process_prompt(update, context, query)
    
    logger.info(f"Response: {response}")
    
    await crossroad(update, context, response)


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
            
            
async def handle_audio_or_text(update, context):
    """Handle audio or text messages."""
    
    if not context.user_data.get('MESSAGE_TEXT'):
        if update.message.voice:
            logger.info("Audio message received.")
            query = await audio_handling(update, context)  # Convert audio to text

        else:
            logger.info("Message received.")
            query = update.message.text

        context.user_data[MESSAGE_TEXT] = query
