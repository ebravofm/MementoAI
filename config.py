from dotenv import load_dotenv
import os

# Cargar las variables desde el archivo .env
load_dotenv()

# Acceder a las variables de entorno
TG_TOKEN = os.getenv("TG_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Validar variables esenciales
if not TG_TOKEN:
    raise ValueError("TG_TOKEN is not set in the environment.")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")