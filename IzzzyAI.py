import asyncio
import logging
import json
import os
import zipfile
import io
import re
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import aiohttp

# ===== НАСТРОЙКИ =====
TELEGRAM_BOT_TOKEN = "8762622437:AAHqXxcXDKEyG7hzRVEtlz4nue78uoDwGa4"

CEREBRAS_API_KEYS = [
    "csk-fek5v5dn9cxj853hfk9cw3hvc24wwn3ddme63tmet8w96dmw",
    "csk-yh2rcf28e6tv9t9tfeynhd5xmfep8xcyc446h3tj3y5yc64j"
]

CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"
CEREBRAS_MODEL = "llama3.1-8b"

REQUIRED_CHANNEL_ID = -1003851572008
REQUIRED_CHANNEL_LINK = "https://t.me/izzzy_vpn"

DAILY_TEXT_LIMIT = 200
DAILY_BOT_LIMIT = 5
# ====================

logging.basicConfig(level=logging.INFO)

user_data_file = "user_data.json"
chat_history_file = "chat_history.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

user_data = load_json(user_data_file)
chat_history = load_json(chat_history_file)

def save_all():
    save_json(user_data_file, user_data)
    save_json(chat_history_file, chat_history)

def get_user(user_id):
    uid = str(user_id)
    if uid not in user_data:
        user_data[uid] = {
            "text_requests_today": 0,
            "bot_requests_today": 0,
            "total_requests": 0,
            "total_bots": 0,
            "last_reset_date": str(date.today()),
            "current_key_index": 0
        }
    if user_data[uid]["last_reset_date"] != str(date.today()):
        user_data[uid]["text_requests_today"] = 0
        user_data[uid]["bot_requests_today"] = 0
        user_data[uid]["last_reset_date"] = str(date.today())
        save_all()
    return user_data[uid]

def get_chat_history(user_id):
    uid = str(user_id)
    if uid not in chat_history:
        chat_history[uid] = []
    return chat_history[uid]

def add_to_history(user_id, role, text):
    uid = str(user_id)
    history = get_chat_history(uid)
    history.append({"role": role, "text": text, "time": str(datetime.now())})
    if len(history) > 30:
        history.pop(0)
    save_json(chat_history_file, chat_history)

async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except:
        return False

async def cerebras_request(messages, user_id=None, max_tokens=500, temperature=0.7):
    if user_id:
        user = get_user(user_id)
        start_index = user.get("current_key_index", 0)
    else:
        start_index = 0
    
    for attempt in range(len(CEREBRAS_API_KEYS)):
        key_index = (start_index + attempt) % len(CEREBRAS_API_KEYS)
        api_key = CEREBRAS_API_KEYS[key_index]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    CEREBRAS_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": CEREBRAS_MODEL,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": 1
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        if user_id:
                            user["current_key_index"] = key_index
                            save_all()
                        return result["choices"][0]["message"]["content"]
                    
                    elif response.status == 429:
                        logging.warning(f"Ключ {key_index+1} лимит, переключение")
                        continue
                    else:
                        continue
                        
        except Exception as e:
            logging.error(f"Ошибка ключа {key_index+1}: {e}")
            continue
    
    return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not await check_subscription(user.id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=REQUIRED_CHANNEL_LINK)]]
        await update.message.reply_text(
            "❌ Чтобы пользоваться ботом, подпишись на канал:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    keyboard = [
        [InlineKeyboardButton("💬 Диалог", callback_data="start_chat")],
        [InlineKeyboardButton("🤖 Создать бота", callback_data="make_bot")],
        [InlineKeyboardButton("📊 Профиль", callback_data="profile")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    
    await update.message.reply_text(
        "🔥 Привет! Я Izzzy AI\n\n"
        "✅ Отвечаю на вопросы\n"
        "✅ Пишу код\n"
        "✅ Создаю Telegram ботов\n\n"
        "👇 Выбери действие:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    
    remaining_text = DAILY_TEXT_LIMIT - user["text_requests_today"]
    remaining_bots = DAILY_BOT_LIMIT - user["bot_requests_today"]
    
    text = f"""📊 Профиль

💬 Текстовые запросы: {user['text_requests_today']}/{DAILY_TEXT_LIMIT}
⏳ Осталось: {remaining_text}

🤖 Создание ботов: {user['bot_requests_today']}/{DAILY_BOT_LIMIT}
⏳ Осталось: {remaining_bots}

📈 Всего запросов: {user['total_requests']}
📦 Всего ботов: {user['total_bots']}"""
    
    keyboard = [[InlineKeyboardButton("◀ Назад", callback_data="back_to_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = f"""❓ Помощь

Команды:
/start - главное меню

Лимиты:
📝 {DAILY_TEXT_LIMIT} текстовых запросов в день
🤖 {DAILY_BOT_LIMIT} созданий ботов в день

🔄 Лимиты обнуляются в 00:00 каждый день"""
    
    keyboard = [[InlineKeyboardButton("◀ Назад", callback_data="back_to_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💬 Диалог", callback_data="start_chat")],
        [InlineKeyboardButton("🤖 Создать бота", callback_data="make_bot")],
        [InlineKeyboardButton("📊 Профиль", callback_data="profile")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    
    await query.edit_message_text(
        "👇 Выбери действие:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def start_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if not await check_subscription(user_id, context):
        await query.edit_message_text("❌ Подпишись на канал чтобы общаться")
        return
    
    user = get_user(user_id)
    if user["text_requests_today"] >= DAILY_TEXT_LIMIT:
        await query.edit_message_text(
            f"⚠️ Дневной лимит ({DAILY_TEXT_LIMIT}) достигнут\n"
            "Жди завтра"
        )
        return
    
    context.user_data["in_chat"] = True
    await query.edit_message_text(
        "💬 Режим диалога включен\n"
        "Просто пиши сообщения, я отвечаю\n\n"
        "Команда /exit - выйти из диалога"
    )

async def make_bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if not await check_subscription(user_id, context):
        await query.edit_message_text("❌ Подпишись на канал чтобы создавать ботов")
        return
    
    user = get_user(user_id)
    if user["bot_requests_today"] >= DAILY_BOT_LIMIT:
        await query.edit_message_text(
            f"⚠️ Дневной лимит ({DAILY_BOT_LIMIT}) созданий ботов достигнут\n"
            "Жди завтра"
        )
        return
    
    await query.edit_message_text(
        "🤖 Опиши какого бота хочешь создать\n\n"
        "Пример:\n"
        "Сделай бота который приветствует пользователя, "
        "отвечает на /start, имеет кнопки 'О нас' и 'Контакты'"
    )
    context.user_data["awaiting_bot_prompt"] = True

async def handle_bot_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_bot_prompt"):
        return
    
    user_id = update.effective_user.id
    prompt_text = update.message.text
    
    await update.message.reply_text("⏳ Генерирую код бота... (может занять до минуты)")
    
    user = get_user(user_id)
    
    # Системный промпт для генерации бота
    system_prompt = """Ты эксперт по написанию Telegram ботов на Python. Сгенерируй полноценного бота по описанию пользователя.

Требования:
- Используй python-telegram-bot версии 20.x
- Код должен быть рабочим без ошибок
- Раздели на несколько файлов: main.py, config.py, handlers.py, keyboards.py
- Добавь requirements.txt
- Напиши инструкцию по запуску в файл README.txt (бесплатные хостинги: PythonAnywhere, Render, Railway, Koyeb)

Формат ответа:
===ФАЙЛ: main.py===
(код)
===ФАЙЛ: config.py===
(код)
===ФАЙЛ: handlers.py===
(код)
===ФАЙЛ: keyboards.py===
(код)
===ФАЙЛ: requirements.txt===
(список библиотек)
===ФАЙЛ: README.txt===
(инструкция по запуску)

Используй понятные имена переменных, добавляй комментарии."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Описание бота: {prompt_text}"}
    ]
    
    response = await cerebras_request(messages, user_id, max_tokens=5000, temperature=0.7)
    
    if not response:
        await update.message.reply_text("❌ Ошибка генерации, попробуй позже")
        context.user_data["awaiting_bot_prompt"] = False
        return
    
    # Парсим файлы
    files = {}
    current_file = None
    current_content = []
    
    for line in response.split('\n'):
        file_match = re.match(r'===ФАЙЛ:\s*(.+?)===', line)
        if file_match:
            if current_file:
                files[current_file] = '\n'.join(current_content)
            current_file = file_match.group(1).strip()
            current_content = []
        elif current_file:
            current_content.append(line)
    
    if current_file:
        files[current_file] = '\n'.join(current_content)
    
    # Создаем ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in files.items():
            zip_file.writestr(filename, content)
    
    zip_buffer.seek(0)
    
    user["bot_requests_today"] += 1
    user["total_bots"] += 1
    save_all()
    
    await update.message.reply_document(
        document=zip_buffer,
        filename=f"bot_{user_id}.zip",
        caption=f"✅ Готово! Бот сгенерирован\nФайлов: {len(files)}"
    )
    
    context.user_data["awaiting_bot_prompt"] = False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    if user_message.startswith('/'):
        return
    
    # Если не в диалоге
    if not context.user_data.get("in_chat"):
        return
    
    if not await check_subscription(user_id, context):
        await update.message.reply_text("❌ Подпишись на канал")
        return
    
    user = get_user(user_id)
    if user["text_requests_today"] >= DAILY_TEXT_LIMIT:
        await update.message.reply_text(f"⚠️ Лимит {DAILY_TEXT_LIMIT} запросов в день исчерпан")
        return
    
    # Получаем историю
    history = get_chat_history(user_id)
    history_messages = []
    for h in history[-20:]:
        history_messages.append({"role": "user" if h["role"] == "user" else "assistant", "content": h["text"]})
    
    messages = [
        {"role": "system", "content": "Ты дружелюбный AI ассистент. Отвечай кратко, по делу, используй нормальные эмодзи (✅, 🔥, ⚠️, 📊, 💬, 🤖, ❓, ◀)."},
        *history_messages,
        {"role": "user", "content": user_message}
    ]
    
    await update.message.chat.send_action(action="typing")
    
    response = await cerebras_request(messages, user_id, max_tokens=500, temperature=0.8)
    
    if response:
        user["text_requests_today"] += 1
        user["total_requests"] += 1
        save_all()
        
        add_to_history(user_id, "user", user_message)
        add_to_history(user_id, "assistant", response)
        
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("❌ Ошибка API, попробуй позже")

async def exit_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["in_chat"] = False
    await update.message.reply_text("👋 Выход из диалога. /start для меню")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("exit", exit_chat))
    
    app.add_handler(CallbackQueryHandler(profile_callback, pattern="profile"))
    app.add_handler(CallbackQueryHandler(help_callback, pattern="help"))
    app.add_handler(CallbackQueryHandler(start_chat_callback, pattern="start_chat"))
    app.add_handler(CallbackQueryHandler(make_bot_callback, pattern="make_bot"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="back_to_menu"))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_prompt))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()