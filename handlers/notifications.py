from telegram.ext import CallbackContext

from utils.logger import logger, tz
from handlers.jobs import get_jobs_from_db

from datetime import datetime, timedelta, time
from handlers.jobs import filter_jobs, delete_jobs
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    

async def notify_next_day_jobs(update, context):
    """Lists all scheduled jobs for the next day in the JobQueue."""
    target_date = datetime.now() + timedelta(days=1)

    # Filtrar trabajos para el día específico
    jobs_for_day = filter_jobs(context, start_date=target_date, end_date=target_date, chat_id=None, job_type='parent')

    # if not jobs_for_day:
    #     await context.bot.send_message(update.effective_chat.id, f"No hay recordatorios programados para {target_date.strftime('%Y-%m-%d')}.")
    #     return

    # Agrupar trabajos por chat_id
    jobs_by_chat = {}
    for job in jobs_for_day:
        chat_id = job.data.get("chat_id")
        if chat_id:
            if chat_id not in jobs_by_chat:
                jobs_by_chat[chat_id] = []
            jobs_by_chat[chat_id].append(job)

    # Enviar un mensaje para cada chat_id
    for chat_id, jobs in jobs_by_chat.items():
        job_list = "\n".join([f"{job.data['Time'].strftime('%H:%M')}: {job.data['Title']}" for job in jobs])
        await context.bot.send_message(
            chat_id,
            f"*Recordatorios para mañana:*\n\n{job_list}",
            parse_mode="markdown",
        )

    
async def notify_next_day_jobs_callback(context: CallbackContext) -> None:
    """Callback to list jobs for the next day."""
    await notify_next_day_jobs(None, context)  # Llama a tu función de listar trabajos para el día siguiente

    
def schedule_daily_notification(job_queue, callback, job_name):
    """Schedules a daily task at 11 PM if it is not already scheduled."""
    # Hora de las 11 PM en UTC (ajustar si usas una zona horaria diferente)
    daily_time = time(23, 0, tzinfo=tz)  # 11 PM
    # daily_time = time(21, 50, tzinfo=tz)  # 11 PM
    
    # Verificar si el trabajo ya está programado
    existing_jobs = [job for job in get_jobs_from_db() if job['name'] == job_name]
    if existing_jobs:
        print(f"Job '{job_name}' is already scheduled.")
        return

    # Programar el trabajo diario
    job_queue.run_daily(
        callback=callback,
        time=daily_time,
        name=job_name,
    )
    print(f"Scheduled job '{job_name}' to run daily at {daily_time}.")
    
async def show_reminder(update, context, name):
    """Show a reminder by its name."""
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.message.chat_id, job_type='parent', name=name)
    if not jobs:
        await update.message.reply_text(f"No se encontró el recordatorio '{name}'.")
        return

    job = jobs[0]
    await update.message.reply_text(job.data['text'], parse_mode="markdown")
    
# async def delete_all_confirmation(update, context):
#     """Confirmar eliminación de todos los recordatorios."""
#     text = "¿Estás seguro de que deseas eliminar todos los recordatorios? Esta acción es irreversible."

#     buttons = [
#         [
#             InlineKeyboardButton(text="Confirmar", callback_data="DELETE_ALL"),
#             InlineKeyboardButton(text="Cancelar", callback_data="CANCELAR"),
#         ]
#     ]
#     keyboard = InlineKeyboardMarkup(buttons)

#     await update.callback_query.answer()
#     await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)


async def delete_all_confirmation(update, context):
    """Confirmar eliminación de todos los recordatorios."""
    text = "¿Estás seguro de que deseas eliminar todos los recordatorios? Esta acción es irreversible."

    buttons = [
        [
            InlineKeyboardButton(text="Confirmar", callback_data="DELETE_ALL"),
            InlineKeyboardButton(text="Cancelar", callback_data="CANCELAR"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text=text, reply_markup=keyboard)
        

async def delete_reminder_confirmation(update, context, name):
    """Confirmar eliminación de un recordatorio especifico."""
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_chat.id, job_type='parent', name=name)
    text = f"¿Estás seguro de que deseas eliminar el siguiente recordatorio?\n\n{jobs[0].data['text']}"

    buttons = [
        [
            InlineKeyboardButton(text="Confirmar", callback_data=f"DELETE_REMINDER {name}"),
            InlineKeyboardButton(text="Cancelar", callback_data="CANCELAR"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="markdown")
    else:
        await update.message.reply_text(text=text, reply_markup=keyboard, parse_mode="markdown")
        
        
async def delete_callback(update, context):
    """Eliminar recordatorios."""
    if update.callback_query.data == "DELETE_ALL":
        delete_jobs(update, context, start_date=None, end_date=None, chat_id=update.effective_chat.id, name=None)
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text="Se borraron todos los recordatorios.")
    elif update.callback_query.data.startswith("DELETE_REMINDER"):
        name = update.callback_query.data.split(" ")[1]
        delete_jobs(update, context, start_date=None, end_date=None, chat_id=update.effective_chat.id, name=name)
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text="Se borró el recordatorio seleccionado.")
    elif update.callback_query.data == "CANCELAR":
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text="Operación cancelada.")