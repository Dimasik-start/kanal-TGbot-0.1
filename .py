import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Храним ID группы для уведомлений
notification_group_id = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🤖 Бот для отслеживания подписок на канал\n\n"
        "Инструкция:\n"
        "1. Добавьте бота в канал как администратора\n"
        "2. Добавьте бота в группу для уведомлений\n"
        "3. В группе отправьте /set_group\n"
        "4. Проверьте настройки командой /check\n\n"
        "Бот должен иметь права администратора в канале!"
    )

async def set_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка группы для уведомлений"""
    global notification_group_id
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ Эту команду нужно использовать в группе или супергруппе!")
        return
    
    notification_group_id = chat_id
    await update.message.reply_text(
        f"✅ Группа настроена для уведомлений!\n"
        f"ID группы: {chat_id}\n"
        f"Теперь добавьте бота в канал как администратора и тестируйте подписки."
    )
    logger.info(f"Notification group set: {chat_id}")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка текущих настроек"""
    global notification_group_id
    
    if notification_group_id:
        await update.message.reply_text(
            f"✅ Настройки:\n"
            f"Группа для уведомлений: {notification_group_id}\n"
            f"Бот готов к работе!"
        )
    else:
        await update.message.reply_text(
            "❌ Настройки не завершены:\n"
            "1. Добавьте бота в группу\n"
            "2. Отправьте /set_group в группе\n"
            "3. Добавьте бота в канал как администратора"
        )

async def debug_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Для отладки - логируем все сообщения"""
    logger.info(f"DEBUG - Message received: {update.message}")

async def my_chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик изменений статуса бота"""
    logger.info(f"MY_CHAT_MEMBER update: {update.my_chat_member}")

async def chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик изменений участников"""
    global notification_group_id
    
    try:
        logger.info(f"CHAT_MEMBER update received!")
        logger.info(f"Full update: {update}")
        
        if update.chat_member:
            chat_member = update.chat_member
            logger.info(f"Chat: {chat_member.chat}")
            logger.info(f"User: {chat_member.from_user}")
            logger.info(f"Old status: {chat_member.old_chat_member.status}")
            logger.info(f"New status: {chat_member.new_chat_member.status}")
            
            # Формируем имя пользователя
            user = chat_member.from_user
            name = user.first_name or ""
            if user.last_name:
                name += f" {user.last_name}"
            if user.username:
                name = f"@{user.username}"
            if not name.strip():
                name = f"User_{user.id}"
            
            # Проверяем изменения статуса
            old_status = chat_member.old_chat_member.status
            new_status = chat_member.new_chat_member.status
            
            if notification_group_id:
                if old_status in ['left', 'kicked'] and new_status == 'member':
                    message = f"✅ {name} подписался на канал"
                    await context.bot.send_message(chat_id=notification_group_id, text=message)
                    logger.info(f"Sent: {message}")
                
                elif old_status == 'member' and new_status in ['left', 'kicked']:
                    message = f"❌ {name} отписался от канала"
                    await context.bot.send_message(chat_id=notification_group_id, text=message)
                    logger.info(f"Sent: {message}")
        
    except Exception as e:
        logger.error(f"Error in chat_member_handler: {e}")

def main():
    """Основная функция"""
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        print("❌ Ошибка: BOT_TOKEN не установлен!")
        return
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_group", set_group))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(MessageHandler(filters.ALL, debug_message))
    
    # Обработчики для отслеживания участников
    application.add_handler(MessageHandler(filters.StatusUpdate.ALL, chat_member_handler))
    
    # Запускаем бота с ВСЕМИ типами обновлений
    print("🤖 Бот запущен с диагностикой...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
