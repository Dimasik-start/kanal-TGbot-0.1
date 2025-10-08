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
# В реальном приложении лучше использовать базу данных
group_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🤖 Бот для отслеживания подписок на канал\n\n"
        "Команды:\n"
        "/set_group - установить группу для уведомлений\n"
        "/info - информация о текущих настройках"
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
        # Получаем информацию об изменении
        chat_member = update.chat_member
        old_chat_member = chat_member.old_chat_member
        new_chat_member = chat_member.new_chat_member
        
        user = chat_member.from_user
        chat = chat_member.chat
        
        # Проверяем, что это канал
        if chat.type != 'channel':
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
                if old_status in ['left', 'kicked'] and new_status == 'member':
                    # Новый подписчик
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=f"✅ {user_display} подписался на канал"
                    )
                    logger.info(f"New subscriber: {user_display}")
                
                elif old_status == 'member' and new_status in ['left', 'kicked']:
                    # Пользователь отписался
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=f"❌ {user_display} отписался от канала"
                    )
                    logger.info(f"Unsubscribed: {user_display}")
                    
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
    application.add_handler(ChatMemberHandler(track_chat_members))
    
    # Запускаем бота
    print("🤖 Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()