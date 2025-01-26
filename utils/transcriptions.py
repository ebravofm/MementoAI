from telegram.ext import ContextTypes
from telegram import Update

from utils.logger import logger
from config import DI_TOKEN

import requests
import io


async def transcribe_voice(voice_file):
    logger.info("Transcribing audio...")
    audio_buffer = io.BytesIO()
    await voice_file.download_to_memory(audio_buffer)

    # Enviar el archivo a la API de OpenAI para transcripción
    audio_buffer.seek(0)  # Asegurarse de que el puntero esté al inicio del archivo

    API_KEY = DI_TOKEN
    API_URL = "https://api.deepinfra.com/v1/inference/openai/whisper-large-v3"


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
        

async def audio_handling(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    voice_file = await context.bot.get_file(update.message.voice.file_id)

    transcription = await transcribe_voice(voice_file)
    logger.info(f"Transcription: {transcription}")
    # reminder = reminder_from_prompt(transcription)
    
    return transcription
