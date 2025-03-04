import datetime
from utils.logger import logger, tz
from smolagents import CodeAgent, OpenAIServerModel
from config import OPENAI_TOKEN
from handlers.misc import send_message, continue_keyboard, tool_keyboards, hide_keyboard
from telegram.ext import ContextTypes


from agents.tools import (
    create_add_reminder_tool,
    create_show_reminders_tool,
    create_get_reminder_details_tool,
    create_delete_all_tool,
    create_delete_by_id_tool,
    create_add_periodic_reminder_tool,
    no_tool_found
)

from utils.constants import (
    MENU
)

from texts.prompts import (
    TXT_MENU_AGENT_SYSTEM_PROMPT,
)
        
        
def base_agent(context: ContextTypes.DEFAULT_TYPE, user_input : str, chat_id: str, prompt: str = TXT_MENU_AGENT_SYSTEM_PROMPT, state: str = 'main_menu'):

    now = datetime.datetime.now(tz).strftime("%d/%m/%Y %H:%M")

    tools = {
        'add_reminder': create_add_reminder_tool(context, chat_id),
        'add_periodic_reminder': create_add_periodic_reminder_tool(context, chat_id),
        'show_reminders': create_show_reminders_tool(context, chat_id),
        'get_reminder_details': create_get_reminder_details_tool(context, chat_id),
        'delete_all': create_delete_all_tool(context, chat_id),
        'delete_by_id': create_delete_by_id_tool(context, chat_id),
        'no_tool_found': no_tool_found
    }

    menu_tool_mapping = {
        'main_menu': tools.values(),
        'add_menu': [tools['add_reminder'], tools['add_periodic_reminder'], tools['no_tool_found']],
        'show_menu': [tools['show_reminders'], tools['get_reminder_details'], tools['no_tool_found']],
        'delete_menu': [tools['delete_all'], tools['delete_by_id'], tools['show_reminders'], tools['no_tool_found']]
    }

    current_tools = menu_tool_mapping.get(state, [])

    agent = CodeAgent(tools=current_tools,
                      additional_authorized_imports=['datetime'],
                      model=OpenAIServerModel(model_id='gpt-4o-mini', api_key=OPENAI_TOKEN),
                      verbosity_level=3,
                      max_steps=6)

    answer = agent.run(prompt.format(user_input=user_input, now=now))

    responses_for_user = {}

    for step in agent.memory.get_full_steps():
        if 'observations' in step:
            try:
                obs = step['observations']
                if "'response_for_user': '" in obs:
                    response_for_user = obs.split("'response_for_user': '")[1].split("'")[0].replace('\\n', '\n')
                    tool_used = obs.split("'tool': '")[1].split("'}")[0]
                    
                    response_data = {
                        'response_for_user': response_for_user,
                        'tool': tool_used,
                        'keyboard': tool_keyboards.get(tool_used, continue_keyboard)
                    }
                    responses_for_user[len(responses_for_user)] = response_data
            except Exception as e:
                logger.error(e)
    
    if not responses_for_user:
        if isinstance(answer, dict):
            answer = answer['message']
            
        responses_for_user[0] = {
            'response_for_user': answer,
            'keyboard': continue_keyboard
        }
            
    return responses_for_user