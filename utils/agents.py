from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.globals import set_debug

from datetime import datetime

from utils.pydantic_models import CategorizePrompt, AllOrOnePrompt, SelectReminderID, LogReminder
from functions.jobs import filter_jobs, get_job_queue_text
from utils.misc import reminder_to_text
from utils.logger import logger
from config import DI_TOKEN


# set_debug(True)

model = ChatOpenAI(temperature=0.7, base_url="https://api.deepinfra.com/v1/openai",
                   api_key=DI_TOKEN,
                   model='meta-llama/Llama-3.3-70B-Instruct',
                   max_tokens=100)


def process_prompt(update, context, query):
    # Paso 1: Clasificación General
    general_parser = JsonOutputParser(pydantic_object=CategorizePrompt)
    general_prompt = PromptTemplate(
        template="""Eres un agente que clasifica prompts en tres categorías:
        
0: **Mostrar recordatorios existentes.** El prompt indica consultar o mostrar los recordatorios ya creados.
1: **Agregar un nuevo recordatorio.** El prompt indica crear un recordatorio con detalles como hora, ubicación o notas.
2: **Eliminar un recordatorio.** El prompt indica eliminar un recordatorio existente.

Devuelve un número entero entre 0 y 2.

.\n{format_instructions}\n{query}\n""",
        input_variables=["query"],
        partial_variables={"format_instructions": general_parser.get_format_instructions()},
    )
    general_chain = general_prompt | model | general_parser
    general_response = general_chain.invoke({"query": query})

    if general_response["category"] == 1:
        return {
            "category": "add_reminder",
        }

    elif general_response["category"] in [0, 2]:

        # Categorías 0 (Mostrar) y 2 (Eliminar)
        action = "show" if general_response["category"] == 0 else "delete"
        all_or_one_parser = JsonOutputParser(pydantic_object=AllOrOnePrompt)
        all_or_one_response = decide_all_or_one(query, model, all_or_one_parser)

        if all_or_one_response["all_reminders"]:
            return {"category": action, "all_reminders": True}
        else:
            # Seleccionar un recordatorio específico
            jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.message.chat_id, job_type='parent')
            reminders_text = get_job_queue_text(update, context)

            id_parser = JsonOutputParser(pydantic_object=SelectReminderID)
            selected_id = int(select_reminder_id(query, reminders_text, model, id_parser)['reminder_id'])
            
            job_name = jobs[selected_id].name
            
            # logger.info(f"Selected job: {selected_job}")
            return {"category": action, "all_reminders": False, "reminder_name": job_name}


def reminder_from_prompt(reminder_query: str) -> LogReminder:

    # Set up a parser + inject instructions into the prompt template.
    parser = JsonOutputParser(pydantic_object=LogReminder)

    now = datetime.now()

    prompt = PromptTemplate(
        template="Convierte el prompt al formato solicitado. Nota: La fecha y hora de referencia son {formatted_now}.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions(), "formatted_now": now.strftime("%Y-%m-%dT%H:%M:%SZ")},
    )

    chain = prompt | model | parser

    response = chain.invoke({"query": reminder_query})
    
    response['Time'] = datetime.strptime(response['Time'][:19], "%Y-%m-%dT%H:%M:%S")

        
    return response


def decide_all_or_one(query, model, parser):
    """Decide if the action applies to all reminders or one specific reminder."""
    prompt = PromptTemplate(
        template="""Eres un agente que decide si la acción del usuario aplica a todos los recordatorios o solo a uno.
        
Responde `True` si la acción aplica a todos los recordatorios, o `False` si aplica solo a un recordatorio específico.

.\n{format_instructions}\n{query}\n""",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | model | parser
    return chain.invoke({"query": query})


def select_reminder_id(query, reminders_text, model, parser):
    """Selecciona el ID de un recordatorio basado en una lista proporcionada."""
    prompt = PromptTemplate(
        template="""Eres un agente que selecciona el ID de un recordatorio basado en la solicitud del usuario.

Estos son los recordatorios disponibles con sus IDs:
{reminders_text}

Devuelve solo el ID numérico correspondiente al recordatorio que el usuario está solicitando.

.\n{format_instructions}\n{query}\n""",
        input_variables=["query", "reminders_text"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | model | parser
    return chain.invoke({"query": query, "reminders_text": reminders_text})


def classify_reminder_type(query, model, parser):
    """Clasifica si un recordatorio es periódico o único."""
    prompt = PromptTemplate(
        template="""Eres un agente que clasifica recordatorios en dos tipos:
        
1. **Periódico (True):** El recordatorio tiene una periodicidad (por ejemplo, todos los días, cada lunes, cada semana a las 8 AM).
2. **Único (False):** El recordatorio ocurre solo una vez (por ejemplo, mañana a las 3 PM).

Devuelve `True` si es periódico o `False` si es único.

.\n{format_instructions}\n{query}\n""",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | model | parser
    return chain.invoke({"query": query})


def decide_all_or_one(query, model, parser):
    """Decide if the action applies to all reminders or one specific reminder."""
    prompt = PromptTemplate(
        template="""Eres un agente que decide si la acción del usuario aplica a todos los recordatorios o solo a uno.
        
Responde `True` si la acción aplica a todos los recordatorios, o `False` si aplica solo a un recordatorio específico.

.\n{format_instructions}\n{query}\n""",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | model | parser
    return chain.invoke({"query": query})


def select_reminder_id(query, reminders_text, model, parser):
    """Selecciona el ID de un recordatorio basado en una lista proporcionada."""
    prompt = PromptTemplate(
        template="""Eres un agente que selecciona el ID de un recordatorio basado en la solicitud del usuario. Nota: La fecha y hora de referencia son {formatted_now}.

Estos son los recordatorios disponibles con sus IDs en paréntesis cuadrados:
{reminders_text}

Devuelve solo el ID numérico correspondiente al recordatorio que el usuario está solicitando.

.\n{format_instructions}\n{query}\n""",
        input_variables=["query", "reminders_text"],
        partial_variables={"format_instructions": parser.get_format_instructions(), "formatted_now": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")},
    )
    chain = prompt | model | parser
    return chain.invoke({"query": query, "reminders_text": reminders_text})


def select_job_by_name(update, context, query):
    
    logger.info("Selecting job by name")
    
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type='parent')
    reminders_text = ""
    for i, job in enumerate(jobs):
        reminders_text += f'[{i}]' + reminder_to_text(job.data) + "\n"

    id_parser = JsonOutputParser(pydantic_object=SelectReminderID)
    selected_id = int(select_reminder_id(query, reminders_text, model, id_parser)['reminder_id'])
    
    job_name = jobs[selected_id].name
    
    return job_name
