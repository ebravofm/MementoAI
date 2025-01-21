from langchain_core.output_parsers import JsonOutputParser
from langchain.globals import set_debug, set_verbose
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from pydantic import BaseModel, Field
from datetime import datetime
from dateutil.parser import isoparse

from config import DI_TOKEN


#set_debug(True)

model = ChatOpenAI(temperature=0.7, base_url="https://api.deepinfra.com/v1/openai",
                   api_key=DI_TOKEN,
                   model='meta-llama/Llama-3.3-70B-Instruct',
                   max_tokens=100)


class LogReminder(BaseModel):
    Title: str = Field(
        description="The title of the reminder."
    )
    Time: str = Field(
        description="The time for the reminder, formatted as an ISO 8601 datetime string."
    )
    Location: str = Field(
        description="The location associated with the reminder."
    )
    Details: str = Field(
        details="Any additional details if there are any."
    )


def reminder_from_prompt(reminder_query: str) -> LogReminder:

    # Set up a parser + inject instructions into the prompt template.
    parser = JsonOutputParser(pydantic_object=LogReminder)

    now = datetime.now()

    prompt = PromptTemplate(
        template="Convert the prompt to the requested format. Note: The reference date and time is {formatted_now}.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions(), "formatted_now": now.strftime("%Y-%m-%dT%H:%M:%SZ")
    },
    )

    chain = prompt | model | parser

    response = chain.invoke({"query": reminder_query})
    
    response['Time'] = isoparse(response['Time'])
    
    return response

def reminder_to_text(reminder: LogReminder) -> str:
    
    reminder['Time_String'] = reminder['Time'].strftime("%H:%M %d/%m/%Y")
    
    text = "📆 *Recordatorio*📆"
    if reminder['Title']:
        text += f"\n*Evento*: {reminder['Title']}"
    if reminder['Time']:
        text += f"\n*Fecha*: {reminder['Time_String']}"
    if reminder['Location']:
        text += f"\n*Ubicación*: {reminder['Location']}"
    if reminder['Details']:
        text += f"\n*Detalle*: {reminder['Details']}"
    
    return text

    # return f"📆 *Recordatorio*\n*Evento*: {reminder['Title']}\n*Fecha*: {reminder['Time']}\n*Ubicación*: {reminder['Location']}\n*Detalle*: {reminder['Details']}"