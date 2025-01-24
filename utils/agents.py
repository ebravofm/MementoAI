from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.globals import set_debug

from config import DI_TOKEN

from pydantic import BaseModel, Field
from datetime import datetime


# set_debug(True)

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
        template="Convierte el prompt al formato solicitado. Nota: La fecha y hora de referencia son {formatted_now}.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions(), "formatted_now": now.strftime("%Y-%m-%dT%H:%M:%SZ")},
    )

    chain = prompt | model | parser

    response = chain.invoke({"query": reminder_query})
    
    try:
        response['Time'] = datetime.strptime(response['Time'], "%Y-%m-%dT%H:%M:%SZ") 
    except ValueError:
        response['Time'] = datetime.strptime(response['Time'], "%Y-%m-%dT%H:%M:%S")
        
    return response

def reminder_to_text(reminder: LogReminder, header = "📆 *Recordatorio*📆\n") -> str:
    
    reminder['Time_String'] = reminder['Time'].strftime("%H:%M %d/%m/%Y")
    
    text = header
    if reminder['Title']:
        text += f"\n*Evento*: {reminder['Title']}"
    if reminder['Time']:
        text += f"\n*Fecha*: {reminder['Time_String']}"
    if reminder['Location']:
        text += f"\n*Ubicación*: {reminder['Location']}"
    if reminder['Details']:
        text += f"\n*Detalle*: {reminder['Details']}"
    
    return text


### CATEGORIZE ###


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


# Paso 2: Clasificación de recordatorios (único o periódico)
class ReminderType(BaseModel):
    is_periodic: bool = Field(
        description=(
            "A boolean value indicating whether the reminder is periodic "
            "(True for periodic, False for one-time reminders)."
        ),
        example=True
    )

# Función para encadenar clasificación
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


# Flujo principal para procesar el prompt
def process_prompt(query, reminders_text, model):
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
        type_parser = JsonOutputParser(pydantic_object=ReminderType)
        reminder_type = classify_reminder_type(query, model, type_parser)
        return {
            "category": "add_reminder",
            "is_periodic": reminder_type["is_periodic"],
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
            id_parser = JsonOutputParser(pydantic_object=SelectReminderID)
            selected_id = select_reminder_id(query, reminders_text, model, id_parser)
            return {"category": action, "all_reminders": False, "reminder_id": selected_id["reminder_id"]}

