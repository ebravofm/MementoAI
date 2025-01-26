from telegram.ext import ConversationHandler

states = [chr(i) for i in range(24)]
(
    MENU, 
    ADD, 
    SHOW, 
    DELETE, 
    ADD_PERIODIC, 
    LISTENING_REMINDER, 
    LISTENING_PERIODIC_REMINDER, 
    SHOW_ALL, 
    SHOW_TODAY, 
    SHOW_TOMORROW, 
    SHOW_WEEK, 
    SHOW_BY_NAME, 
    LISTENING_TO_SHOW_BY_NAME, 
    DELETE_ALL, 
    DELETE_BY_NAME, 
    CONFIRM_DELETE_ALL, 
    CONFIRMED_DELETE_ALL, 
    LISTENING_TO_DELETE_BY_NAME, 
    CONFIRM_DELETE_BY_NAME, 
    CONFIRMED_DELETE_BY_NAME, 
    START_OVER, 
    START_WITH_NEW_REPLY, 
    STOPPING, 
    MESSAGE_TEXT
) = states

END = ConversationHandler.END