
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils.logger import logger

from utils.constants import (
    START_OVER,
    START_WITH_NEW_REPLY,
    MESSAGE_TEXT,
    MENU,
    END,
    ADD,
    SHOW,
    DELETE
)

import locale
locale.setlocale(locale.LC_TIME, "es_ES")





async def end_second_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[START_OVER] = True
    await start(update, context)
    return MENU


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Ok, nos vemos!.")
    return END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    text = "See you around!"
    await update.callback_query.edit_message_text(text=text)
    return END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    try:
        await update.callback_query.message.reply_text("Se produjo un error, volviendo al menú principal.")
    except AttributeError:
        await update.effective_message.reply_text("Se produjo un error, volviendo al menú principal.")
    
    # Limpiar el estado y volver al menú principal
    context.user_data['START_OVER'] = True
    context.user_data['START_WITH_NEW_REPLY'] = True
    context.user_data['MESSAGE_TEXT'] = None
    
    await start(update, context)
    
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = '''🤖 *Bienvenido a MementoAI 🤖*

MementoAI es un asistente de recordatorios que te ayuda a gestionar tus recordatorios de manera fácil y eficiente.


*Comandos*

• `/start`: Inicia la conversación con MementoAI.
• `/menu`: Muestra el menú principal de MementoAI.
• `/stop`: Detiene la conversación con MementoAI.
• `/help`: Muestra esta ayuda para que puedas aprender a utilizar MementoAI.


*Funcionalidades*

• Agregar recordatorios
• Mostrar recordatorios
• Eliminar recordatorios
• Agregar recordatorios periódicos
• Notificaciones diarias de recordatorios


*Uso*

1. Inicia la conversación con MementoAI utilizando el comando `/start`.
2. Puedes interactuar con MementoAI de dos maneras:
    • Utilizando el menú y los botones para seleccionar la opción que deseas.
    • Escribiendo o hablando directamente con el bot, y este entenderá y hará lo que le pides. Por ejemplo, puedes decir "Agregar un recordatorio" o "Mostrar mis recordatorios de hoy".
3. Sigue las instrucciones para agregar, mostrar o eliminar recordatorios.


*Notas importantes*

• Cuando veas los iconos `[📝/🎙️]`, significa que puedes escribir o hablar con el bot para darle instrucciones. El icono `📝` representa la escritura de texto, y el icono `🎙️` representa la voz.
• Puedes utilizar este formato para dar instrucciones al bot en cualquier momento.


*Ejemplos de comandos de voz o texto*

• "Agregar un recordatorio para mañana a las 10am"
• "Mostrar mis recordatorios de hoy"
• "Eliminar el recordatorio de la reunión de esta tarde"
'''
    await update.effective_message.reply_text(help_text, parse_mode="markdown")
    


# Top level conversation callbacks
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Selecciona una acción: Agregar recordatorio, mostrar recordatorios o eliminar recordatorios."""
    
    full_text = "🤖 *Bienvenid@ a MementoAI* 🤖\n\nEstoy aquí para ayudarte a gestionar tus recordatorios de manera fácil y eficiente.\n\n¿En qué puedo ayudarte? \[📝/🎙️]"
    text_then = "¿En qué más puedo ayudarte? \[📝/🎙️]"
    buttons = [
        [
            InlineKeyboardButton(text="📝 Agregar nuevo recordatorio", callback_data=str(ADD)),
        ],
        [
            InlineKeyboardButton(text="📄 Ver recordatorios", callback_data=str(SHOW)),
            InlineKeyboardButton(text="❌ Eliminar recordatorios", callback_data=str(DELETE)),
        ],    
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    logger.info(context.user_data)
    if context.user_data.get(START_OVER):
        if context.user_data.get(START_WITH_NEW_REPLY):
            await context.bot.send_message(update.effective_chat.id, text=text_then, reply_markup=keyboard, parse_mode="markdown")
        else:
            try:
                await update.callback_query.edit_message_text(text=text_then, reply_markup=keyboard, parse_mode="markdown")
            except AttributeError:
                await context.bot.send_message(update.effective_chat.id, text=text_then, reply_markup=keyboard, parse_mode="markdown")
    else:
        logger.info('test1')
        await update.effective_message.reply_text(text=full_text, reply_markup=keyboard, parse_mode="markdown")
        # await context.bot.send_message(update.effective_chat.id, text=full_text, reply_markup=keyboard, parse_mode="markdown")

    context.user_data[START_OVER] = False
    context.user_data[START_WITH_NEW_REPLY] = False
    context.user_data[MESSAGE_TEXT] = None
    return MENU