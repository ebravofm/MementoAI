PROMPT_FORMAT_REMINDER = "Convierte el prompt al formato solicitado. Solo puedes programar recordatorios en el futuro. Nota: La fecha y hora actuales son {formatted_now}.\n{format_instructions}\n{query}\n"

PROMPT_SELECT_REMINDER = """Eres un agente que selecciona el ID de un recordatorio basado en la solicitud del usuario. Nota: La fecha y hora de referencia son {formatted_now}. \n Estos son los recordatorios disponibles con sus IDs en paréntesis cuadrados: \n {reminders_text}.\nDevuelve solo el ID numérico correspondiente al recordatorio que el usuario está solicitando.\n{format_instructions}\n{query}\n"""

PROMPT_DECIDE_ALL_OR_ONE = """Eres un agente que decide si la acción del usuario aplica a todos los recordatorios o solo a uno. \nResponde `True` si la acción aplica a todos los recordatorios, o `False` si aplica solo a un recordatorio específico.\n{format_instructions}\n{query}\n"""

PROMPT_CLASSIFY_ACTION = """Eres un agente que clasifica prompts en tres categorías:
0: **Mostrar recordatorios existentes.** El prompt indica consultar o mostrar los recordatorios ya creados.
1: **Agregar un nuevo recordatorio.** El prompt indica crear un recordatorio con detalles como hora, ubicación o notas.
2: **Eliminar un recordatorio.** El prompt indica eliminar un recordatorio existente.
Devuelve un número entero entre 0 y 2.\n\n{format_instructions}\n{query}\n"""