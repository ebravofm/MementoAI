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