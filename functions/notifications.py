from telegram.ext import CallbackContext, ContextTypes

from functions.jobs import get_jobs_from_db, filter_jobs
from utils.logger import logger, tz

from datetime import datetime, timedelta, time


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    logger.info(f"Alarm triggered for chat_id {job.chat_id} with data: {job.data['text']}")
    await context.bot.send_message(job.chat_id, text=job.data['text'], parse_mode="markdown")


async def alarm_minus_30(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    logger.info(f"Alarm triggered for chat_id {job.chat_id} with data: {job.data['text']}")
    
    text = 'Faltan *30 minutos* para:\n' + job.data['Title']
    
    await context.bot.send_message(job.chat_id, text=text, parse_mode="markdown")


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
    
    
async def notify_next_day_jobs_callback(context: CallbackContext) -> None:
    """Callback to list jobs for the next day."""
    await notify_next_day_jobs(None, context)  # Llama a tu función de listar trabajos para el día siguiente