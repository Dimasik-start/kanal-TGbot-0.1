import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ChatMemberHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Храним ID группы для уведомлений
notification_group_id = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот для отслеживания подписок. Используйте /set_group в группе для настройки уведомлений."
    )

async def set_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global notification_group_id
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ Команда работает только в группах!")
        return
    
    notification_group_id = chat_id
    await update.message.reply_text(f"✅ Группа настроена для уведомлений! ID: {chat_id}")
    logger.info(f"Notification group set: {chat_id}")

def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обновлений участников"""
    try:
        # Безопасное получение данных
        if not update.chat_member:
            return
            
        change = update.chat_member
        old_status = change.old_chat_member.status if change.old_chat_member else None
        new_status = change.new_chat_member.status if change.new_chat_member else None
        
        if not old_status or not new_status:
            return
            
        user = change.from_user
        chat = change.chat
        
        # Только для каналов
        if chat.type != 'channel':
            return
        
        # Формируем имя пользователя
        name = user.first_name or ""
        if user.last_name:
            name += f" {user.last_name}"
        if user.username:
            name = f"@{user.username}"
        if not name.strip():
            name = f"User_{user.id}"
        
        # Проверяем изменения
        if notification_group_id:
            if old_status in ['left', 'kicked'] and new_status == 'member':
                context.bot.send_message(
                    notification_group_id, 
                    f"✅ {name} подписался на канал"
                )
            elif old_status == 'member' and new_status in ['left', 'kicked']:
                context.bot.send_message(
                    notification_group_id, 
                    f"❌ {name} отписался от канала"
                )
                    
    except Exception as e:
        logger.error(f"Chat member error: {e}")

def main():
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ Установите BOT_TOKEN в .env файле!")
        return
        
    app = Application.builder().token(bot_token).build()
    
    # Обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_group", set_group))
    app.add_handler(ChatMemberHandler(handle_chat_member_update))
    
    print("🤖 Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
