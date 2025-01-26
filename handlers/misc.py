
from telegram import Update
from telegram.ext import ContextTypes

from handlers.delete import confirm_delete_all, confirm_delete_by_name
from handlers.show import show_all, show_by_name
from utils.misc import handle_audio_or_text
from handlers.add import add_reminder_timer
from utils.agents import process_prompt
from utils.logger import logger
from commands import start
from utils.constants import (
    START_OVER,
    MESSAGE_TEXT,
    MENU
)


async def categorize_and_reply(update, context):
    """Categorizes a prompt into three categories."""
    
    await handle_audio_or_text(update, context)
    query = context.user_data.get(MESSAGE_TEXT)

    response = process_prompt(update, context, query)
    
    logger.info(f"Response: {response}")
    
    await crossroad(update, context, response)


async def crossroad(update, context, response):

    if response["category"] == "add_reminder":
        await add_reminder_timer(update, context)
                        
    elif response["category"] == "show":
        if response["all_reminders"]:
            await show_all(update, context)
        else:
            await show_by_name(update, context, name=response["reminder_name"])

    elif response["category"] == "delete":
        if response["all_reminders"]:
            await confirm_delete_all(update, context)
        else:
            await confirm_delete_by_name(update, context)
                     

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    # await update.message.reply_text(update.message.text)
    # await context.bot.send_message(update.effective_chat.id, text=update.message.text, parse_mode="markdown")
    await update.message.reply_text(update.message.text)
    logger.info(update.message.text)
    
    context.user_data[START_OVER] = True
    await start(update, context)

    return MENU