from dotenv import load_dotenv
import os

# Cargar las variables desde el archivo .env
load_dotenv()

# Acceder a las variables de entorno
TG_TOKEN = os.getenv("TG_TOKEN")
DI_TOKEN = os.getenv("DI_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
DS_TOKEN = os.getenv("DS_TOKEN")
MODEL_ID_OPENAI = os.getenv("MODEL_ID_OPENAI")
BASE_URL_OPENAI = os.getenv("BASE_URL_OPENAI")
MODEL_ID_DI = os.getenv("MODEL_ID_DI")
BASE_URL_DI = os.getenv("BASE_URL_DI")

# Validar variables esenciales
if not TG_TOKEN:
    raise ValueError("TG_TOKEN is not set in the environment.")
if not DI_TOKEN:
    raise ValueError("DI_TOKEN is not set in the environment.")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")
if not OPENAI_TOKEN:
    raise ValueError("OPENAI_TOKEN is not set in the environment.")
if not DS_TOKEN:
    raise ValueError("DS_TOKEN is not set in the environment.")
if not MODEL_ID_OPENAI:
    raise ValueError("MODEL_ID_OPENAI is not set in the environment.")
if not BASE_URL_OPENAI:
    raise ValueError("BASE_URL_OPENAI is not set in the environment.")
if not MODEL_ID_DI:
    raise ValueError("MODEL_ID_DI is not set in the environment.")
if not BASE_URL_DI:
    raise ValueError("BASE_URL_DI is not set in the environment.")
