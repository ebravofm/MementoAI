import requests
import io
import logging
import pytz
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
import pickle
from config import DATABASE_URL

tz = pytz.timezone("America/Santiago")  # Adjust according to your timezone


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)



async def transcribe_voice(voice_file):

    audio_buffer = io.BytesIO()
    await voice_file.download_to_memory(audio_buffer)

    # Enviar el archivo a la API de OpenAI para transcripción
    audio_buffer.seek(0)  # Asegurarse de que el puntero esté al inicio del archivo

    API_KEY = "cSZCVvh6PZe7bRy8qRtvoDeU3nS9XwdQ"
    API_URL = "https://api.deepinfra.com/v1/inference/openai/whisper-large-v3-turbo"


    headers = {
        "Authorization": f"bearer {API_KEY}"
    }
    files = {
        "audio": ("my_voice.mp3", audio_buffer, "audio/mpeg")
    }

    # Hacer la solicitud a la API
    response = requests.post(API_URL, headers=headers, files=files)

    # Manejar la respuesta de la API
    if response.status_code == 200:
        transcription = response.json().get("text", "No se pudo obtener la transcripción")
        return transcription
    else:
        response.raise_for_status()
        
        
def get_jobs():
    # Crear el motor de conexión con SQLAlchemy
    engine = create_engine(DATABASE_URL)

    # Crear la sesión
    Session = sessionmaker(bind=engine)
    session = Session()

    # Reflejar la tabla apscheduler_jobs
    metadata = MetaData()
    metadata.reflect(bind=engine)
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

    # Cerrar la sesión
    session.close()
    
    job_states = [job_state for job_state in job_states if job_state is not None]
    
    return job_states