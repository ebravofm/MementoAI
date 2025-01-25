from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from utils.agents import model, reminder_to_text
from handlers.jobs import filter_jobs
from utils.logger import logger
from datetime import datetime


def get_reminders_text(update, context):
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.message.chat_id, job_type='parent')
    text = ""
    for i, job in enumerate(jobs):
        text += f'[{i}]' + reminder_to_text(job.data) + "\n"
        
    return text
    

# Flujo principal para procesar el prompt
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
            reminders_text = ""
            for i, job in enumerate(jobs):
                reminders_text += f'[{i}]' + reminder_to_text(job.data) + "\n"

            id_parser = JsonOutputParser(pydantic_object=SelectReminderID)
            selected_id = int(select_reminder_id(query, reminders_text, model, id_parser)['reminder_id'])
            
            job_name = jobs[selected_id].name
            
            # logger.info(f"Selected job: {selected_job}")
            return {"category": action, "all_reminders": False, "reminder_name": job_name}


# Paso 1: Clasificación General
class CategorizePrompt(BaseModel):
    category: int = Field(
        description=(
            "An integer value indicating the category of the prompt:\n"
            "0: Show existing reminders.\n"
            "1: Add a new reminder.\n"
            "2: Delete a reminder."
        ),
        example=1
    )

# Paso 2: Decidir si se aplica a todos los recordatorios o a uno específico
class AllOrOnePrompt(BaseModel):
    all_reminders: bool = Field(
        description=(
            "A boolean value indicating whether the action applies to all reminders "
            "(True for all, False for a specific reminder)."
        ),
        example=True
    )

# Paso 3: Seleccionar el ID del recordatorio si aplica a uno específico
class SelectReminderID(BaseModel):
    reminder_id: int = Field(
        description="The numeric ID of the reminder that the user wants to select.",
        example=42
    )

# Función para decidir si la acción aplica a todos o a uno
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

# Función para seleccionar un ID de recordatorio
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
    query = update.effective_message.text
    jobs = filter_jobs(context, start_date=None, end_date=None, chat_id=update.effective_message.chat_id, job_type='parent')
    reminders_text = ""
    for i, job in enumerate(jobs):
        reminders_text += f'[{i}]' + reminder_to_text(job.data) + "\n"

    id_parser = JsonOutputParser(pydantic_object=SelectReminderID)
    selected_id = int(select_reminder_id(query, reminders_text, model, id_parser)['reminder_id'])
    
    job_name = jobs[selected_id].name
    
    return job_name
