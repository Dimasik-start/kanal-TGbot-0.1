import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ChatMemberHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Словарь для хранения ID групп для уведомлений
group_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🤖 Бот для отслеживания подписок на канал\n\n"
        "Команды:\n"
        "/set_group - установить группу для уведомлений\n"
        "/info - информация о текущих настройках\n\n"
        "⚠️ Важно: Бот должен быть администратором в канале!"
    )

async def set_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /set_group"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    # Проверяем, что команда вызвана в группе или супергруппе
    if chat_type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ Эту команду нужно использовать в группе или супергруппе!")
        return
    
    # Сохраняем ID группы
    group_chats[chat_id] = chat_id
    await update.message.reply_text(
        f"✅ Группа настроена для уведомлений!\n"
        f"ID группы: {chat_id}\n"
        f"Теперь бот будет отправлять сюда уведомления о подписках/отписках."
    )
    logger.info(f"Group set for notifications: {chat_id}")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /info"""
    chat_id = update.effective_chat.id
    if chat_id in group_chats:
        await update.message.reply_text(f"✅ Эта группа настроена для уведомлений (ID: {chat_id})")
    else:
        await update.message.reply_text("❌ Эта группа не настроена для уведомлений. Используйте /set_group")

async def track_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик изменений в участниках канала"""
    try:
        logger.info(f"Received chat member update: {update}")
        
        # Получаем информацию об изменении
        chat_member = update.chat_member
        if not chat_member:
            logger.error("No chat_member in update")
            return
            
        old_chat_member = chat_member.old_chat_member
        new_chat_member = chat_member.new_chat_member
        
        user = chat_member.from_user
        chat = chat_member.chat
        
        logger.info(f"Chat: {chat.title} (ID: {chat.id}, Type: {chat.type})")
        logger.info(f"User: {user.first_name} (ID: {user.id})")
        logger.info(f"Old status: {old_chat_member.status}")
        logger.info(f"New status: {new_chat_member.status}")
        
        # Проверяем, что это канал
        if chat.type != 'channel':
            logger.info(f"Not a channel, skipping. Chat type: {chat.type}")
            return
        
        # Получаем статусы пользователя
        old_status = old_chat_member.status
        new_status = new_chat_member.status
        
        # Формируем имя пользователя
        username = user.username
        if username:
            user_display = f"@{username}"
        else:
            user_display = f"{user.first_name or ''} {user.last_name or ''}".strip()
            if not user_display:
                user_display = f"Пользователь (ID: {user.id})"
        
        # Отправляем уведомления во все настроенные группы
        for group_id in group_chats.values():
            try:
                if old_status in ['left', 'kicked', 'restricted'] and new_status in ['member', 'administrator']:
                    # Новый подписчик
                    message = f"✅ {user_display} подписался на канал"
                    await context.bot.send_message(chat_id=group_id, text=message)
                    logger.info(f"Sent subscription notification: {message}")
                
                elif old_status in ['member', 'administrator'] and new_status in ['left', 'kicked', 'restricted']:
                    # Пользователь отписался
                    message = f"❌ {user_display} отписался от канала"
                    await context.bot.send_message(chat_id=group_id, text=message)
                    logger.info(f"Sent unsubscription notification: {message}")
                else:
                    logger.info(f"No relevant status change: {old_status} -> {new_status}")
                    
            except Exception as e:
                logger.error(f"Error sending message to group {group_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in track_chat_members: {e}")

def main():
    """Основная функция для запуска бота"""
    # Получаем токен бота из переменных окружения
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        print("❌ Ошибка: BOT_TOKEN не установлен!")
        print("Создайте файл .env и добавьте: BOT_TOKEN=your_bot_token_here")
        return
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_group", set_group))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(ChatMemberHandler(track_chat_members, ChatMemberHandler.CHAT_MEMBER))
    
    # Запускаем бота
    print("🤖 Бот запущен...")
    logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
