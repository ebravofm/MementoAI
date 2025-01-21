from telegram.ext import CallbackContext
from datetime import datetime, timedelta, time
from utils import logger, tz, get_jobs

    
async def notify_next_day_jobs(update, context):
    """Lists all scheduled jobs for a specific day in the JobQueue."""
    
    target_date = datetime.now() + timedelta(days=1)

    # Get all jobs from the JobQueue
    jobs = context.job_queue.jobs()

    if not jobs:
        logger.info("No jobs are currently scheduled.")
        return

    # Filter jobs for the specific day
    jobs_for_day = [
        job for job in jobs
        if job.next_run_time.date() == target_date.date() and job.data is not None
    ]

    if not jobs_for_day:
        logger.info(f"No jobs scheduled for {target_date.strftime('%Y-%m-%d')}.")
        return

    # Group jobs by chat_id
    jobs_by_chat = {}
    for job in jobs_for_day:
        chat_id = job.data.get("chat_id")
        if chat_id:
            if chat_id not in jobs_by_chat:
                jobs_by_chat[chat_id] = []
            jobs_by_chat[chat_id].append(job)

    # Send a message for each chat_id
    for chat_id, jobs in jobs_by_chat.items():
        job_list = "\n".join([f"{job.data['Time'].strftime('%H:%M')}: {job.data['Title']}" for job in jobs])
        await context.bot.send_message(
            chat_id,
            f"*Recordatorios para mañana:*\n\n{job_list}",
            parse_mode="markdown",
        )

    
async def notify_next_day_jobs_callback(context: CallbackContext) -> None:
    """Callback to list jobs for the next day."""
    job_queue = context.job_queue
    for job in job_queue.jobs():
        print(job.name)
    await notify_next_day_jobs(None, context)  # Llama a tu función de listar trabajos para el día siguiente

    
def schedule_daily_notification(job_queue, callback, job_name):
    """Schedules a daily task at 11 PM if it is not already scheduled."""
    # Hora de las 11 PM en UTC (ajustar si usas una zona horaria diferente)
    daily_time = time(11, 0, tzinfo=tz)  # 11 PM
    
    # Verificar si el trabajo ya está programado
    existing_jobs = [job for job in get_jobs() if job['name'] == job_name]
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

