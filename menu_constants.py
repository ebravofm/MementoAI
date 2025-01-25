from telegram.ext import ConversationHandler


MENU = chr(0)
ADD = chr(1)
SHOW = chr(2)
DELETE = chr(3)
ADD_PERIODIC = chr(4)
LISTENING_REMINDER = chr(5)
LISTENING_PERIODIC_REMINDER = chr(6)
SHOW_ALL = chr(7)
SHOW_TODAY = chr(8)
SHOW_TOMORROW = chr(9)
SHOW_WEEK = chr(10)
SHOW_BY_NAME = chr(11)
DELETE_ALL = chr(12)
DELETE_BY_NAME = chr(13)
START_OVER = chr(14)
START_WITH_NEW_REPLY = chr(15)
STOPPING = chr(16)

END = ConversationHandler.END