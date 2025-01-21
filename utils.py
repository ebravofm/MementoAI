import requests
import io

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