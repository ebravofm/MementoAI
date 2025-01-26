from pydantic import BaseModel, Field
from typing import Tuple


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


class AllOrOnePrompt(BaseModel):
    all_reminders: bool = Field(
        description=(
            "A boolean value indicating whether the action applies to all reminders "
            "(True for all, False for a specific reminder)."
        ),
        example=True
    )


class SelectReminderID(BaseModel):
    reminder_id: int = Field(
        description="The numeric ID of the reminder that the user wants to select.",
        example=42
    )


class ReminderType(BaseModel):
    is_periodic: bool = Field(
        description=(
            "A boolean value indicating whether the reminder is periodic "
            "(True for periodic, False for one-time reminders)."
        ),
        example=True
    )
    
    
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


class AllOrOnePrompt(BaseModel):
    all_reminders: bool = Field(
        description=(
            "A boolean value indicating whether the action applies to all reminders "
            "(True for all, False for a specific reminder)."
        ),
        example=True
    )


class SelectReminderID(BaseModel):
    reminder_id: int = Field(
        description="The numeric ID of the reminder that the user wants to select.",
        example=42
    )

    
class DailyReminder(BaseModel):
    Time: str = Field(
        description="The time for the reminder, formatted as an ISO 8601 time string."
    )
    Days: Tuple[int, ...] = Field(
        default=(0, 1, 2, 3, 4, 5, 6),
        description="Defines on which days of the week the job should run (where 0-6 correspond to sunday - saturday). By default, the job will run every day."
    )
    Title: str = Field(
        description="The title of the reminder."
    )
    Details: str = Field(
        default='',
        description="Any additional details if there are any."
    )