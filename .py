import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ChatMemberHandler

print("🤖 Запуск бота для отслеживания подписок...")

NOTIFICATION_GROUP = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    await update.message.reply_text(
        "📢 Бот для отслеживания подписок на канал\n\n"
        "Как настроить:\n"
        "1. Добавить бота в КАНАЛ как администратора\n"
        "2. Включить право 'Изменение чужих сообщений'\n"
        "3. Добавить бота в ГРУППУ для уведомлений\n"
        "4. Отправить /set_group в группе"
    )

async def set_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    print(f"✅ Группа для уведомлений установлена: {chat_id}")

async def handle_member_changes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global NOTIFICATION_GROUP
    try:
        if update.chat_member is None:
            return
        change = update.chat_member
        if (change.old_chat_member is None or 
            change.new_chat_member is None or 
            change.from_user is None or 
            change.chat is None):
            return
        old_status = change.old_chat_member.status
        new_status = change.new_chat_member.status
        user = change.from_user
        chat = change.chat
        print(f"🔔 Обновление в канале '{chat.title}':")
        print(f"   👤 Пользователь: {user.first_name}")
        print(f"   📊 Статус: {old_status} -> {new_status}")
        if chat.type != 'channel':
            return
        if user.username:
            name = f"@{user.username}"
        else:
            name = user.first_name or f"ID{user.id}"
        if NOTIFICATION_GROUP:
            if old_status in ['left', 'kicked'] and new_status == 'member':
                message = f"✅ {name} подписался на канал"
                await context.bot.send_message(NOTIFICATION_GROUP, message)
                print(f"📢 Отправлено: {message}")
            elif old_status == 'member' and new_status in ['left', 'kicked']:
                message = f"❌ {name} отписался от канала"
                await context.bot.send_message(NOTIFICATION_GROUP, message)
                print(f"📢 Отправлено: {message}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ ОШИБКА: Установите BOT_TOKEN в Secrets!")
        return
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_group", set_group))
    app.add_handler(ChatMemberHandler(handle_member_changes, ChatMemberHandler.CHAT_MEMBER))
    print("✅ Бот запущен и готов к работе!")
    print("⏳ Ожидаю обновления о подписках...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
