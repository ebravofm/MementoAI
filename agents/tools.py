import datetime
from utils.logger import logger, tz
from utils.misc import reminder_to_text
from functions.notifications import alarm, alarm_minus_30
from smolagents import tool
from typing import List
from functions.jobs import filter_jobs, print_jobs
import traceback

from texts.texts import (
    TXT_NOT_ABLE_TO_SCHEDULE_PAST,
    TXT_REMINDER_SCHEDULED,
    TXT_NO_REMINDERS_TO_DELETE,
    TXT_CONFIRM_DELETE_ALL,
    TXT_CONFIRM_DELETE_BY_NAME,
    TXT_NO_TOOL_FOUND,
    TXT_NO_REMINDERS_SCHEDULED
)

from agents.text_completion import text_completion

from texts.prompts import (
    TXT_CHOOSE_ANSWER_PROMPT
)


def create_show_reminders_tool(context, chat_id):
    @tool
    def show_reminders(start_date: datetime = None, end_date: datetime = None) -> dict:
        """
        Lists  scheduled jobs between start_date and end_date in the JobQueue grouped by day. If start_date and end_date are not provided, all jobs are shown. If user asks for a single reminder, then use the show_specific_reminder tool. Returns a message to be sent to the user.
        
        Args:
            start_date: The start date for the filter (inclusive). Optional.
            end_date: The end date for the filter (inclusive). Optional.
            
        Returns:
            A dictionary with the following
            success: A boolean indicating if the operation was successful
            message: The message to be sent to the user
        """
        if isinstance(start_date, str):
            return {'success': False, 'message': 'start_date debe ser un objeto datetime, Ej. datetime.datetime(2022, 1, 1)', 'tool':'show_reminders'}
        
        try:
            # Filtrar trabajos usando la función filter_jobs
            jobs = filter_jobs(job_queue=context.job_queue, chat_id=chat_id, job_type='parent', start_date=start_date, end_date=end_date)
            
            if jobs:
                result = [{'job_id': job.id[-5:] , 'job_data': job.data} for job in jobs]
                response_for_user = print_jobs(jobs, show_periodic=True)
                return {'success': True, 'result': result, 'response_for_user': response_for_user, 'tool': 'show_reminders'}
                
            else:
                response_for_user = TXT_NO_REMINDERS_SCHEDULED
                return {'success': True, 'response_for_user': response_for_user, 'tool': 'show_reminders'}

    
        except Exception as e:
            logger.error(traceback.format_exc())
            return {'success': False, 'message': traceback.format_exc(), 'tool': 'show_reminders'}
    
    return show_reminders


def create_get_reminder_details_tool(context, chat_id):
    @tool
    def get_reminder_details(job_id: str) -> dict:
        """
        Get the details of a reminder by job_id. Use if user wants to see the details of a specific reminder. Use the show_all tool to get the job_id. Returns a message to be sent to the user.
        
        Args:
            job_id: The job_id of the reminder to be shown
            
        Returns:
            A dictionary with the following
            success: A boolean indicating if the operation was successful
            message: The message to be sent to the user
        """
        
        jobs = filter_jobs(job_queue=context.jobs_queue, chat_id=chat_id, job_type=None, job_id=job_id)
        
        job = jobs[0]
        
        response_for_user = job.data['text']
        
        return {'success': True, 'response_for_user': response_for_user, 'tool': 'get_reminder_details'}
    
    return get_reminder_details
    


def create_add_reminder_tool(context, chat_id):
    @tool
    def add_reminder(title: str,
                     date_time: datetime.datetime,
                     location: str = None,
                     details: str = None) -> dict:
        
        '''
        Add a reminder to the job queue.
        
        Args:
        title: The title of the reminder  (str)
        date_time: The time for the reminder
        location: The location of the reminder if it is specified. If not then None (str)
        details: The details of the reminder if it is specified. If not then None (str)
        '''
        
        # try:
        reminder = {}
        reminder['Title'] = title
        reminder['Time'] = date_time
        reminder['Location'] = location
        reminder['Details'] = details
        reminder['chat_id'] = chat_id

        # Convert the reminder time string to a localized datetime object
        timer_date = date_time.replace(tzinfo=None)
        timer_date = tz.localize(timer_date)
        timer_date_string = timer_date.strftime("%H:%M %d/%m/%Y")

        timer_name = f"{title} ({timer_date_string})"
        reminder['run'] = 'once'
        reminder['text'] = reminder_to_text(reminder)

        # Calculate the time remaining in seconds
        now = datetime.datetime.now(tz)
        seconds_until_due = (timer_date - now).total_seconds()

        # Check if the time is in the past
        if seconds_until_due <= 0:
            return {'success': False, 'response_for_agent': TXT_NOT_ABLE_TO_SCHEDULE_PAST, 'tool': 'add_reminder'}

        reminder['type'] = 'parent'
        
        context.job_queue.run_once(
            alarm,
            when=timer_date,
            chat_id=chat_id,
            name=timer_name,
            data=reminder,
            job_kwargs = {'misfire_grace_time': None}
        )
        
        reminder['type'] = '-30'
        context.job_queue.run_once(
            alarm_minus_30,
            when=timer_date - datetime.timedelta(minutes=30),
            chat_id=chat_id,
            name=timer_name,
            data=reminder,
        )
            
        return {'success': True, 'message': TXT_REMINDER_SCHEDULED, 'response_for_user': reminder['text'], 'tool': 'add_reminder'}
    
    return add_reminder



def create_add_periodic_reminder_tool(context, chat_id):
    @tool
    def add_periodic_reminder(title: str,
                              time: datetime.time,
                              days: List[int],
                              details: str = None) -> dict:
        
        '''
        Add a periodic reminder to the job queue. A periodic reminder is a reminder that repeats on specific days of the week. Returns a message to be sent to the user.
        
        Args:
            title: The title of the reminder  (str)
            days: A tuple of integers representing the days of the week when the reminder should be scheduled. 0 is Sunday and 6 is Saturday. 0 = Sunday, 1 = Monday, 2 = Tuesday, 3 = Wednesday, 4 = Thursday, 5 = Friday, 6 = Saturday.  (Tuple[int, ...])
            time: The time for the reminder (datetime.time)
            details: The details of the reminder if it is specified. If not then None (str)
            
        Returns:
            A dictionary with the following
            success: A boolean indicating if the operation was successful
            message: The message to be sent to the user
        '''

        # Generate reminder from the text
        # reminder = periodic_reminder_from_prompt(query)
        try:
            reminder = {}
            reminder['Title'] = title
            reminder['Time'] = time
            reminder['Days'] = days
            reminder['Details'] = details
            reminder['chat_id'] = chat_id


            # Convert the reminder time to a localized datetime object
            timer_date = reminder['Time'].replace(tzinfo=tz)
            # timer_date = tz.localize(timer_date)
            timer_date_string = timer_date.strftime("%H:%M:%S")

            timer_name = f"{reminder['Title']} ({reminder['Days']})"
            reminder['run'] = 'periodic'
            reminder['text'] = reminder_to_text(reminder)

            
            reminder['type'] = 'parent'
            context.job_queue.run_daily(
                alarm,
                time=timer_date,
                days=reminder['Days'],
                chat_id=chat_id,
                name=timer_name,
                data=reminder,
            )            

            return {'success': True, 'message': TXT_REMINDER_SCHEDULED, 'response_for_user': TXT_REMINDER_SCHEDULED+'\n\n'+reminder['text'], 'tool': 'add_periodic_reminder'}
        
        except Exception as e:
            logger.error(traceback.format_exc())
            return {'success': False, 'message': traceback.format_exc(), 'response_for_user': 'Hubo un error al programar el recordatorio. Inténtalo de nuevo.', 'tool': 'add_periodic_reminder'}
        
    return add_periodic_reminder




def create_delete_all_tool(context, chat_id):
    @tool
    def delete_all() -> dict:
        """
        Delete all reminders. Returns a message to be sent to the user.
        
        Args:
            None
            
        Returns:
            A dictionary with the following
            success: A boolean indicating if the operation was successful
            message: The message to be sent to the user
        """
        logger.info("Eliminando todos los recordatorios.")
        jobs = filter_jobs(job_queue=context.job_queue, start_date=None, end_date=None, chat_id=chat_id, job_type=None)

        if not jobs:
            return {'success': False, 'response_for_user': TXT_NO_REMINDERS_TO_DELETE, 'tool': 'delete_all'}
                        
        return {'success': True, 'response_for agent': 'The user will be asked for confirmation, you can close now with a final answer', 'response_for_user': TXT_CONFIRM_DELETE_ALL, 'tool': 'delete_all'}

    return delete_all


def create_delete_by_id_tool(context, chat_id):
    @tool 
    def delete_by_id(job_id: str) -> dict:
        """
        Delete reminders by job_id. Only use if user wants to delete a specific reminder. Use the show_all tool to get the job_id. Returns a message to be sent to the user. 
        
        Args:
            job_id: The job_id of the reminder to be deleted
            
        Returns:
            A dictionary with the following
            success: A boolean indicating if the operation was successful
            message: The message to be sent to the user
        """
        
        jobs = filter_jobs(job_queue=context.job_queue, chat_id=chat_id, job_type=None)
        logger.info(f'jobs: {jobs}')
        jobs = filter_jobs(job_queue=context.job_queue, chat_id=chat_id, job_type=None, job_id=job_id)
        logger.info(f'jobs: {jobs}')
        
        if not jobs:
            return {'success': False, 'response_for_user': TXT_NO_REMINDERS_TO_DELETE, 'tool': 'delete_by_id'}
        
        job_name = jobs[0].name

        
        context.user_data['JOB_TO_DELETE'] = job_name
            
        return {'success': True, 'response_for agent': 'The user will be asked for confirmation, you can close now with a final answer', 'response_for_user': TXT_CONFIRM_DELETE_BY_NAME.format(name=job_name), 'tool': 'delete_by_id'}
            
    return delete_by_id

@tool
def no_tool_found() -> dict:
    '''
    This tool is called when no tool is found for the user input.
    
    Args:
       None
    '''
    return {'success': False, 'response_for_user': TXT_NO_TOOL_FOUND}
        
        
def choose_answer(user_input: str, options: dict):
    
    try:
        options = str(options)
        prompt = TXT_CHOOSE_ANSWER_PROMPT.format(user_input=user_input, options=options)

        reponse = text_completion(prompt, max_tokens=10, stop=None)

        index = int([l for l in reponse if l.isdigit()][0])
        
        logger.info(prompt+'\n\n'+str(index))
        
        return index
    
    except Exception as e:
        raise e