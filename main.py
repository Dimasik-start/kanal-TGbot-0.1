import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, ChatMemberHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ID группы для уведомлений
NOTIFICATION_GROUP = None

def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    update.message.reply_text(
        "📊 Трекер Подписчиков - отслеживание подписок и отписок\n\n"
        "Как настроить:\n"
        "1. Добавить бота в КАНАЛ как администратора\n"
        "2. Включить право 'Изменение чужих сообщений'\n"
        "3. Добавить бота в ГРУППУ для уведомлений\n"
        "4. Отправить /set_group в группе"
    )

def set_group(update: Update, context: CallbackContext):
    """Установка группы для уведомлений"""
    global NOTIFICATION_GROUP
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    if chat_type not in ['group', 'supergroup']:
        update.message.reply_text("❌ Используйте эту команду в группе!")
        return
    
    NOTIFICATION_GROUP = chat_id
    update.message.reply_text(f"✅ Группа настроена! ID: {chat_id}")
    logger.info(f"Группа для уведомлений установлена: {chat_id}")

def handle_member_changes(update: Update, context: CallbackContext):
    """Обработчик подписок/отписок"""
    global NOTIFICATION_GROUP
    
    try:
        if update.chat_member is None:
            return
            
        change = update.chat_member
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
                context.bot.send_message(NOTIFICATION_GROUP, message)
                logger.info(f"Отправлено: {message}")
            
            # Отписка
            elif old_status == 'member' and new_status in ['left', 'kicked']:
                message = f"❌ {name} отписался от канала"
                context.bot.send_message(NOTIFICATION_GROUP, message)
                logger.info(f"Отправлено: {message}")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")

def main():
    """Основная функция запуска"""
    token = os.getenv('BOT_TOKEN')
    
    if not token:
        logger.error("❌ ОШИБКА: Установите BOT_TOKEN в переменные окружения!")
        return
        
    # Используем Updater вместо Application для версии 13.x
    updater = Updater(token, use_context=True)
    
    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher
    
    # Регистрируем обработчики
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("set_group", set_group))
    dp.add_handler(ChatMemberHandler(handle_member_changes))
    
    # Запускаем бота
    logger.info("✅ Бот запущен и готов к работе!")
    print("🤖 Бот запущен! Ожидаю обновления...")
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
