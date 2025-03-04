
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import datetime
from utils.logger import logger, tz
from smolagents import CodeAgent, OpenAIServerModel
from config import OPENAI_TOKEN
from handlers.misc import send_message, continue_keyboard, tool_keyboards, hide_keyboard
from handlers.audio import audio_handling
from agents.agents import base_agent

from agents.tools import (
    choose_answer
)

from utils.constants import (
    MENU
)

from texts.texts import (
    TXT_PROCESSING,
)

from texts.prompts import (
    TXT_MENU_AGENT_SYSTEM_PROMPT,
    TXT_DELETE_AGENT_SYSTEM_PROMPT
)

async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await base_handler(update, context, state='main_menu')
    return MENU


async def add_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await base_handler(update, context, state='add_menu')
    return MENU


async def show_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await base_handler(update, context, state='show_menu')
    return MENU


async def delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await base_handler(update, context, state='delete_menu', prompt=TXT_DELETE_AGENT_SYSTEM_PROMPT)
    return MENU


async def base_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt:str = TXT_MENU_AGENT_SYSTEM_PROMPT, state='main_menu'):
    
    msg = await send_message(update, context, text=TXT_PROCESSING)
    
    if update.message.voice:
        logger.info("Audio message received.")
        user_input = await audio_handling(update, context)  # Convert audio to text
    else:
        user_input = update.message.text
        
    chat_id = update.effective_chat.id
    
    responses_for_user = base_agent(context, user_input=user_input, chat_id=chat_id, prompt=prompt, state=state)
        
    if responses_for_user:
        if len(responses_for_user) == 1:
            response_data = next(iter(responses_for_user.values()))
            msg = await send_message(update, context, text=response_data['response_for_user'], keyboard=response_data['keyboard'], edit=True, msg=msg)
        else:
            options = {k: v['response_for_user'] for k, v in responses_for_user.items()}
            i = choose_answer(user_input=prompt.format(user_input=user_input, now=None), options=options)
            response_data = responses_for_user[i]
            msg = await send_message(update, context, text=response_data['response_for_user'], keyboard=response_data['keyboard'], edit=True, msg=msg)

    await hide_keyboard(update, context, msg=msg)