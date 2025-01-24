from telegram.ext import ContextTypes
from telegram import Update

from config import DATABASE_URL
from utils.logger import logger

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from collections import defaultdict
import pickle


async def list_jobs(update, context, start_date: datetime = None, end_date: datetime = None, header="Recordatorios Programados"):
    """Lists all scheduled jobs in the JobQueue grouped by day."""
    # Filtrar trabajos usando la función filter_jobs
    jobs = filter_jobs(context, start_date=start_date, end_date=end_date, chat_id=update.message.chat_id, job_type='parent')

    if not jobs:
        await update.message.reply_text("No hay recordatorios programados.")
        return

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
    await update.message.reply_text(message, parse_mode="markdown")


def filter_jobs(context, start_date: datetime = None, end_date: datetime = None, chat_id: int = None, job_type: str = 'parent', name: str = None) -> list:
    """
    Filtra los trabajos según un rango de fechas, chat_id, tipo de trabajo y nombre de trabajo.

    :param context: Contexto del bot.
    :param start_date: Fecha inicial para el filtro (inclusive). Opcional.
    :param end_date: Fecha final para el filtro (inclusive). Opcional.
    :param chat_id: ID del chat para el filtro. Opcional.
    :param job_type: Tipo de trabajo para el filtro. Opcional, por defecto None.
    :param name: Nombre del trabajo para el filtro. Opcional.
    :return: Lista de trabajos que cumplen con los criterios de filtro.
    """
    jobs = context.job_queue.jobs()
    filtered_jobs = [
        job for job in jobs
        if job.data is not None and
        (start_date is None or start_date.date() <= job.data['Time'].date()) and
        (end_date is None or job.data['Time'].date() <= end_date.date()) and
        (chat_id is None or job.data['chat_id'] == chat_id) and
        (job_type is None or job.data.get('type') == job_type) and
        (name is None or name in job.name)
    ]
    return filtered_jobs

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

        
def get_jobs_from_db():
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


def delete_jobs(update, context, start_date: datetime = None, end_date: datetime = None, chat_id: int = None, name: str = None):
    """Delete jobs from the JobQueue and the database."""
    jobs = filter_jobs(context, start_date=start_date, end_date=end_date, chat_id=chat_id, name=name, job_type=None)
    if not jobs:
        #update.message.reply_text("No se encontraron trabajos para eliminar.")
        context.bot.send_message(chat_id=chat_id, text="No se encontraron trabajos para eliminar.")
        return

    for job in jobs:
        job.schedule_removal()