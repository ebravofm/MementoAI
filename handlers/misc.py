from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from telegram import InputMediaPhoto

from texts.texts import (
    TXT_BUTTON_CONTINUE,
    TXT_BUTTON_CONFIRM,
    TXT_BUTTON_CANCEL,
    TXT_BUTTON_BACK
)
from utils.constants import (
    MENU,
    CONFIRMED_DELETE_ALL,
    END,
    CONFIRMED_DELETE_BY_NAME,
    BACK
)

from utils.logger import logger

async def send_message(update: Update,
                       context: ContextTypes.DEFAULT_TYPE,
                       text: str = None,
                       media: str = None,
                       keyboard: InlineKeyboardMarkup = None,
                       disable_web_page_preview = True,
                       edit: bool = False,
                       msg = None):
        
    if edit:
        try:
            if media:
                
                if msg:
                    media = InputMediaPhoto(media=open(media, 'rb'), caption=text, parse_mode="markdown", disable_web_page_preview=disable_web_page_preview)
                    msg = await msg.edit_media(media=media, reply_markup=keyboard)

                else: 
                    media = InputMediaPhoto(media=open(media, 'rb'), caption=text, parse_mode="markdown")
                    msg = await update.effective_message.edit_media(media=media, reply_markup=keyboard)
                
            else:
                try:
                    if msg:
                        msg = await msg.edit_text(text=text, parse_mode="markdown", disable_web_page_preview=disable_web_page_preview, reply_markup=keyboard)
                    else:
                        msg = await update.effective_message.edit_text(text=text, parse_mode="markdown", disable_web_page_preview=disable_web_page_preview, reply_markup=keyboard)
                except BadRequest:
                    try:
                        if msg:
                            await msg.delete()
                        else:
                            await update.effective_message.delete()
                    except BadRequest:
                        logger.info("Couldn't delete message")
                    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode="markdown", disable_web_page_preview=disable_web_page_preview, reply_markup=keyboard)
                    
        except AttributeError:
            if media:
                msg = await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(media, 'rb'), caption=text, parse_mode="markdown", reply_markup=keyboard)
            else:
                msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode="markdown", disable_web_page_preview=disable_web_page_preview, reply_markup=keyboard)
                
    else:
        if media:
            msg = await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(media, 'rb'), caption=text, parse_mode="markdown", reply_markup=keyboard)
        else:
            msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode="markdown", disable_web_page_preview=disable_web_page_preview, reply_markup=keyboard)
            

    return msg



async def hide_keyboard(update, context, msg=None, disable_web_page_preview=True):
    
    
    if msg:
        
        chat_id=msg.chat_id
        message_id=msg.message_id
        text = msg.text_markdown
        
        if text:
            logger.debug(f"Storing to hide keyboard with message: {text}")
            context.user_data['HIDE_KEYBOARD'] = {'chat_id': chat_id,
                                                  'message_id': message_id,
                                                  'text': text}
    else:
        msg_info = context.user_data.get('HIDE_KEYBOARD')

        if msg_info:

            try:
                chat_id = msg_info['chat_id']
                message_id = msg_info['message_id']
                text = msg_info['text']

                logger.debug(f"Hiding keyboard with message: {text}")
                await context.bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, parse_mode="markdown", disable_web_page_preview=disable_web_page_preview)
            except BadRequest as e:
                logger.debug(f"Couldn't hide keyboard: {e}")

            context.user_data['HIDE_KEYBOARD'] = None
                
        else:
            logger.debug("No message to hide keyboard")



continue_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=TXT_BUTTON_CONTINUE, callback_data=str(MENU))]
        ])

confirm_delete_all_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text=TXT_BUTTON_CONFIRM, callback_data=str(CONFIRMED_DELETE_ALL)),
            InlineKeyboardButton(text=TXT_BUTTON_CANCEL, callback_data=str(END)),
        ]
    ])

confirm_delete_by_id_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text=TXT_BUTTON_CONFIRM, callback_data=str(CONFIRMED_DELETE_BY_NAME)),
            InlineKeyboardButton(text=TXT_BUTTON_CANCEL, callback_data=str(END)),
        ]
    ])

back_keyboard = InlineKeyboardMarkup([
        [
        InlineKeyboardButton(text=TXT_BUTTON_BACK, callback_data=str(BACK)),
        ]
    ])


tool_keyboards = {
    'show_reminders': continue_keyboard,
    'show_specific_reminder': continue_keyboard,
    'add_reminder': continue_keyboard,
    'add_periodic_reminder': continue_keyboard,
    'delete_by_id': confirm_delete_by_id_keyboard,
    'delete_all': confirm_delete_all_keyboard
}