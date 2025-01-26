from telegram.ext import ContextTypes

from utils.misc import reminder_to_text
from config import DATABASE_URL

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pickle


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
        (start_date is None or start_date.date() <= job.next_run_time.date()) and
        (end_date is None or job.next_run_time.date() <= end_date.date()) and
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


def get_job_queue_text(update, context):
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.message.chat_id, job_type='parent')
    text = ""
    for i, job in enumerate(jobs):
        text += f'[{i}]' + reminder_to_text(job.data) + "\n"
        
    return text
    
