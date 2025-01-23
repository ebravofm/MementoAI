from telegram.ext import ContextTypes
from telegram import Update

from config import DATABASE_URL

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from collections import defaultdict
import pickle

        
def get_jobs():
    # Crear el motor de conexión con SQLAlchemy
    engine = create_engine(DATABASE_URL)

    # Crear la sesión
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Reflejar la tabla apscheduler_jobs
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        if "apscheduler_jobs" not in metadata.tables:
            print("Table 'apscheduler_jobs' does not exist.")
            return []

        apscheduler_jobs = Table("apscheduler_jobs", metadata, autoload_with=engine)

        # Obtener y deserializar los valores de la columna job_state
        job_states = []
        with engine.connect() as connection:
            query = apscheduler_jobs.select().with_only_columns([apscheduler_jobs.c.job_state])
            result = connection.execute(query)

            for row in result:
                binary_data = row.job_state  # Ya es de tipo bytes

                # Deserializar usando pickle
                try:
                    deserialized_data = pickle.loads(binary_data)
                    job_states.append(deserialized_data)
                except Exception as e:
                    print(f"Error deserializing job_state: {e}")
                    job_states.append(None)

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

    finally:
        # Cerrar la sesión
        session.close()

    # Filtrar valores válidos
    job_states = [job_state for job_state in job_states if job_state is not None]
    
    return job_states

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)

async def list_jobs(update, context):
    """Lists all scheduled jobs in the JobQueue grouped by day."""
    # Obtener todos los trabajos de la JobQueue
    jobs = context.job_queue.jobs()
    jobs = [job for job in jobs if '-30' not in job.name]
    

    if not jobs:
        await update.message.reply_text("No jobs are currently scheduled.")
        return

    # Agrupar trabajos por día
    jobs_by_day = defaultdict(list)
    for job in jobs:
        if job.data and "Time" in job.data and "Title" in job.data:
            job_day = job.next_run_time.date()
            jobs_by_day[job_day].append(job)

    # Formatear la lista de trabajos por día
    message = "*Scheduled Jobs:*\n"
    for day, jobs in sorted(jobs_by_day.items()):
        day_str = day.strftime("%A %d %B")  # Ejemplo: Tuesday 23 January 2025
        message += f"\n*{day_str}*:\n"
        message += "\n".join(
            [f"  - {job.data['Time'].strftime('%H:%M')}: {job.data['Title']}" for job in jobs]
        )
        message += "\n"

    # Enviar el mensaje al usuario
    await update.message.reply_text(message, parse_mode="markdown")




async def list_jobs_for_week(update, context, start_date: datetime):
    """Lists all scheduled jobs for the remaining days of the week in the JobQueue."""
    # Get all jobs from the JobQueue
    jobs = context.job_queue.jobs()

    if not jobs:
        await update.message.reply_text("No jobs are currently scheduled.")
        return

    # Define the start of the remaining week (start_date) and end of the week (Sunday)
    today = datetime.now()
    start_of_remaining_week = max(today, start_date)
    end_date = start_of_remaining_week + timedelta(days=(6 - start_of_remaining_week.weekday()))

    # Filter jobs for the remaining days of the week
    jobs_for_week = [
        job for job in jobs
        if start_of_remaining_week.date() <= job.next_run_time.date() <= end_date.date()
    ]

    if not jobs_for_week:
        await update.message.reply_text(
            f"No jobs scheduled for the remaining week from {start_of_remaining_week.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}.")
        return

    # Format the job list
    job_list = "\n".join([f"- {job.name} ({job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')})" for job in jobs_for_week])

    await update.message.reply_text(
        f"Jobs for the remaining week from {start_of_remaining_week.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}:\n{job_list}")


async def list_jobs_for_day(update, context, target_date: datetime):
    """Lists all scheduled jobs for a specific day in the JobQueue."""
    # Get all jobs from the JobQueue
    jobs = context.job_queue.jobs()
    jobs = [job for job in jobs if '-30' not in job.name]

    if not jobs:
        await update.message.reply_text("No jobs are currently scheduled.")
        return

    # Filter jobs for the specific day
    jobs_for_day = [
        job for job in jobs
        if job.next_run_time.date() == target_date.date() and job.data is not None
    ]

    if not jobs_for_day:
        await update.message.reply_text(f"No jobs scheduled for {target_date.strftime('%Y-%m-%d')}.")
        return

    # Format the job list
    job_list = "\n".join([f"{job.data['Time'].strftime('%H:%M')}: {job.data['Title']}" for job in jobs_for_day])

    await update.message.reply_text(f"*Recordatorios para el {target_date.strftime('%d/%m')}:*\n\n{job_list}", parse_mode="markdown")


async def list_jobs_for_current_day(update, context):
    """Lists all scheduled jobs for the current day."""
    await list_jobs_for_day(update, context, datetime.now())


async def list_jobs_for_next_day(update, context):
    """Lists all scheduled jobs for the next day."""
    next_day = datetime.now() + timedelta(days=1)
    await list_jobs_for_day(update, context, next_day)


async def list_jobs_for_current_week(update, context):
    """Lists all scheduled jobs for the current week."""
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    await list_jobs_for_week(update, context, start_of_week)


async def list_jobs_for_next_week(update, context):
    """Lists all scheduled jobs for the next week."""
    today = datetime.now()
    start_of_next_week = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
    await list_jobs_for_week(update, context, start_of_next_week)
    