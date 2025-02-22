from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from telegram import InputMediaPhoto


async def send_message(update: Update,
                       context: ContextTypes.DEFAULT_TYPE,
                       text: str = None,
                       media: str = None,
                       keyboard: InlineKeyboardMarkup = None,
                       disable_web_page_preview = True,
                       edit: bool = False,
                       msg = None,
                       category = None,
                       ai_text_id = None):
    
    # logger.info(f"Sending message: {text}")
    
    text = text.encode('utf-8', errors='replace')
    text = text.decode('utf-8')
    
    
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
            
            
    # msg_data = {
    #     'tg_msg_id': str(msg.message_id),
    #     'tg_chat_id': str(msg.chat_id),
    #     'user_id': str(update.effective_user.id),
    #     'type': 'sent',
    #     'category': category,
    #     'text': text,
    #     'ai_text_id': ai_text_id
    # }
    
    # with get_db() as db:
    #     create_message(db, MessageCreate(**msg_data))
        
    return msg

