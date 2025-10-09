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

# ID группы для уведомлений
NOTIFICATION_GROUP = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    if update.message is None:
        return
        
    await update.message.reply_text(
        "📊 Трекер Подписчиков - отслеживание подписок и отписок\n\n"
        "Как настроить:\n"
        "1. Добавить бота в КАНАЛ как администратора\n"
        "2. Включить право 'Изменение чужих сообщений'\n"
        "3. Добавить бота в ГРУППУ для уведомлений\n"
        "4. Отправить /set_group в группе"
    )

async def set_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка группы для уведомлений"""
    global NOTIFICATION_GROUP
    
    if update.message is None or update.effective_chat is None:
        return
        
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    if chat_type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ Используйте эту команду в группе!")
        return
    
    NOTIFICATION_GROUP = chat_id
    await update.message.reply_text(f"✅ Группа настроена! ID: {chat_id}")
    logger.info(f"Группа для уведомлений установлена: {chat_id}")

async def handle_member_changes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик подписок/отписок"""
    global NOTIFICATION_GROUP
    
    try:
        if update.chat_member is None:
            return
            
        change = update.chat_member
        
        # Проверяем необходимые атрибуты
        if (change.old_chat_member is None or 
            change.new_chat_member is None or 
            change.from_user is None or 
            change.chat is None):
            return
            
        old_status = change.old_chat_member.status
        new_status = change.new_chat_member.status
        user = change.from_user
        chat = change.chat
        
        logger.info(f"Обновление в канале '{chat.title}': {user.first_name} - {old_status} -> {new_status}")
        
        # Работаем только с каналами
        if chat.type != 'channel':
            return
            
        # Формируем имя для уведомления
        if user.username:
            name = f"@{user.username}"
        else:
            name = user.first_name or f"ID{user.id}"
        
        # Отправляем уведомления
        if NOTIFICATION_GROUP:
            # Новая подписка
            if old_status in ['left', 'kicked'] and new_status == 'member':
                message = f"✅ {name} подписался на канал"
                await context.bot.send_message(NOTIFICATION_GROUP, message)
                logger.info(f"Отправлено: {message}")
            
            # Отписка
            elif old_status == 'member' and new_status in ['left', 'kicked']:
                message = f"❌ {name} отписался от канала"
                await context.bot.send_message(NOTIFICATION_GROUP, message)
                logger.info(f"Отправлено: {message}")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")

def main():
    """Основная функция запуска"""
    token = os.getenv('BOT_TOKEN')
    
    if not token:
        logger.error("❌ BOT_TOKEN не установлен!")
        print("❌ Установите BOT_TOKEN в переменные окружения!")
        return
        
    # Создаем приложение
    app = Application.builder().token(token).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_group", set_group))
    app.add_handler(ChatMemberHandler(handle_member_changes, ChatMemberHandler.CHAT_MEMBER))
    
    logger.info("✅ Бот запущен и готов к работе!")
    print("🤖 Бот запущен на Render!")
    
    # Запускаем бота
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
