from telegram.ext import ContextTypes
from telegram import Update


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text("""¡Hola! Aquí tienes los comandos disponibles para interactuar con el bot:

*Comandos básicos:*
- **`/start`**: Inicia el bot y muestra un mensaje de bienvenida.
- **`/help`**: Muestra esta lista de comandos y su descripción.

*Gestión de recordatorios:*
- **`/list`**: Muestra todos los trabajos (tareas) programados en el sistema.
- **`/list_day`**: Muestra las tareas programadas para hoy.
- **`/list_next_day`**: Muestra las tareas programadas para el día siguiente.
- **`/list_week`**: Muestra las tareas pendientes para el resto de la semana, desde el día actual hasta el domingo.
- **`/list_next_week`**: Muestra las tareas programadas para la próxima semana completa (de lunes a domingo).

*Creación de recordatorios:*
- Puedes crear recordatorios enviando un mensaje de texto o un mensaje de voz. El bot procesará la información y programará un recordatorio según el contenido proporcionado.

*Notificaciones automáticas:*
- Cada día, a las 11:00 PM, recibirás una notificación con las tareas programadas para el día siguiente.""", parse_mode="markdown")
    

