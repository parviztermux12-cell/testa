import asyncio
import logging
import json
import os
import zipfile
import io
import re
from datetime import datetime, date, timedelta
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import aiohttp

# ===== НАСТРОЙКИ =====
TELEGRAM_BOT_TOKEN = "8762622437:AAHQ6PhA5iBxsNVXNd7SaCR3_jqE2j21LeM"  # ЗАМЕНИ НА ТОКЕН ОТ @BotFather
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "tinyllama:1.1b"
REQUIRED_CHANNEL_ID = -1003851572008
REQUIRED_CHANNEL_LINK = "https://t.me/izzzy_vpn"
# ====================

logging.basicConfig(level=logging.INFO)

# Хранилище данных
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
            "last_reset_date": str(date.today())
        }
    # Сброс лимитов если новый день
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
    if len(history) > 50:
        history.pop(0)
    save_json(chat_history_file, chat_history)

async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except:
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться на канал", url=REQUIRED_CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🍁 *Добро пожаловать в Izzzy AI!*\n\n"
            f"Чтобы пользоваться ботом, подпишитесь на наш канал:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    keyboard = [
        [InlineKeyboardButton("🍌 Начать разговор", callback_data="start_chat")],
        [InlineKeyboardButton("🥬 Сделать бота", callback_data="make_bot")],
        [InlineKeyboardButton("📊 Мой профиль", callback_data="profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🍁 *Добро пожаловать в Izzzy AI* - наша модель работает через виртуальный сервер, "
        f"он ещё обучается и может давать не точные ответы на ваши вопросы.\n\n"
        f"🍌 *Я умею:*\n"
        f"• Генерировать текстовые ответы\n"
        f"• Общаться в группах\n"
        f"• Делать готовый код по описанию для вашего Telegram бота (могут быть иногда ошибки)\n\n"
        f"👇 *Выберите действие:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    
    remaining_text = 150 - user["text_requests_today"]
    remaining_bots = 5 - user["bot_requests_today"]
    
    text = (
        f"📊 *Твой профиль*\n\n"
        f"💬 *Текстовые запросы:* {user['text_requests_today']}/150 сегодня\n"
        f"💠 *Осталось текстовых:* {remaining_text}\n\n"
        f"🤖 *Создание ботов:* {user['bot_requests_today']}/5 сегодня\n"
        f"⚙️ *Осталось созданий:* {remaining_bots}\n\n"
        f"📈 *Всего запросов:* {user['total_requests']}\n"
        f"📦 *Всего создано ботов:* {user['total_bots']}"
    )
    await query.edit_message_text(text, parse_mode="Markdown")

async def start_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.first_name
    
    if not await check_subscription(user_id, context):
        await query.edit_message_text("❌ *Подпишись на канал чтобы общаться!*")
        return
    
    user = get_user(user_id)
    if user["text_requests_today"] >= 150:
        await query.edit_message_text(
            "💠 *Дневной лимит достигнут!*\n"
            "Ожидайте следующего дня чтобы продолжить.",
            parse_mode="Markdown"
        )
        return
    
    # Генерация приветствия от ИИ
    history = get_chat_history(user_id)
    history_text = "\n".join([f"{h['role']}: {h['text']}" for h in history[-10:]])
    
    prompt = f"""Ты дружелюбный ИИ-помощник Izzzy. Ты всегда общаешься на русском языке. 
Отвечай кратко или средне (2-4 предложения), но не длинно. Используй эмодзи иногда.
Твоя задача - поприветствовать пользователя {username} и предложить ему задать любой вопрос.

История диалога (если есть):
{history_text}

Напиши приветствие пользователю {username}:"""
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 100, "temperature": 0.8}
    }
    
    await query.edit_message_text("💭 *Запускаю ИИ...*", parse_mode="Markdown")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OLLAMA_URL, json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    bot_reply = result.get("response", "Привет! Чем могу помочь?")
                    
                    user["text_requests_today"] += 1
                    user["total_requests"] += 1
                    save_all()
                    
                    add_to_history(user_id, "user", "/start")
                    add_to_history(user_id, "assistant", bot_reply)
                    
                    await query.edit_message_text(bot_reply, parse_mode="Markdown")
                    context.user_data["in_chat"] = True
                else:
                    await query.edit_message_text("❌ Ошибка, попробуй позже")
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def make_bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if not await check_subscription(user_id, context):
        await query.edit_message_text("❌ *Подпишись на канал чтобы создавать ботов!*")
        return
    
    user = get_user(user_id)
    if user["bot_requests_today"] >= 5:
        await query.edit_message_text(
            "💠 *Дневной лимит созданий ботов достигнут!*\n"
            "Ожидайте следующего дня чтобы продолжить.",
            parse_mode="Markdown"
        )
        return
    
    await query.edit_message_text(
        "🥬 *Это наш тестовый режим!*\n\n"
        "Здесь вы можете сделать своего телеграмм бота с помощью нашей нейросети. "
        "Код может содержать ошибки (редко), наша модель ещё не обучена до конца, "
        "после написания кода бота, он вам кинет в zip файле все его данные.\n"
        "В день можете делать максимум 5 таких запросов.",
        parse_mode="Markdown"
    )
    
    await asyncio.sleep(2)
    
    await query.edit_message_text(
        "🍌 *Киньте пожалуйста промт*, описав подробнее функционал который хотите увидеть в своем боте, "
        "я улучшу и сгенерирую код.",
        parse_mode="Markdown"
    )
    context.user_data["awaiting_prompt"] = True

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_prompt"):
        return
    
    user_id = update.effective_user.id
    prompt_text = update.message.text
    
    keyboard = [
        [InlineKeyboardButton("✅ Да", callback_data="confirm_gen")],
        [InlineKeyboardButton("❌ Нет", callback_data="cancel_gen")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🇳🇵 *Промт взят. Начать генерацию кода?*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    context.user_data["bot_prompt"] = prompt_text
    context.user_data["awaiting_prompt"] = False

async def confirm_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    await query.edit_message_text("🍁 *Ожидайте...*\n(Генерация может занять от 10 секунд до 20 минут)", parse_mode="Markdown")
    
    user = get_user(user_id)
    prompt_text = context.user_data.get("bot_prompt", "")
    
    # Генерация кода бота
    code_prompt = f"""Напиши полный код Telegram бота на Python с использованием python-telegram-bot версии 20.x.
    
Требования к боту:
{prompt_text}

Важно:
- Используй русский язык для всех текстов (кнопки, сообщения, подписи)
- Раздели код по модулям (разные файлы)
- Создай requirements.txt со всеми нужными библиотеками
- Код должен быть без ошибок
- Добавь обработку команд /start, /help
- Сделай красивый интерфейс с кнопками

Верни ответ в формате:
Файл: main.py
(код)
---
Файл: config.py
(код)
---
Файл: requirements.txt
(библиотеки)"""
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": code_prompt,
        "stream": False,
        "options": {"num_predict": 4096, "temperature": 0.7}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OLLAMA_URL, json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    code_response = result.get("response", "")
                    
                    # Создаем ZIP файл
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        # Парсим ответ и создаем файлы
                        current_file = None
                        current_content = []
                        
                        for line in code_response.split('\n'):
                            if line.startswith('Файл: '):
                                if current_file:
                                    zip_file.writestr(current_file, '\n'.join(current_content))
                                current_file = line.replace('Файл: ', '').strip()
                                current_content = []
                            elif line.startswith('---'):
                                continue
                            else:
                                current_content.append(line)
                        
                        if current_file:
                            zip_file.writestr(current_file, '\n'.join(current_content))
                        
                        # Добавляем requirements если его нет
                        try:
                            zip_file.getinfo('requirements.txt')
                        except KeyError:
                            zip_file.writestr('requirements.txt', 'python-telegram-bot==20.7\naiohttp==3.9.0')
                    
                    zip_buffer.seek(0)
                    
                    user["bot_requests_today"] += 1
                    user["total_bots"] += 1
                    save_all()
                    
                    await query.edit_message_text("✅ *Готово! Вот твой бот:*", parse_mode="Markdown")
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=zip_buffer,
                        filename=f"{user_id}_bot.zip"
                    )
                    context.user_data["bot_prompt"] = None
                else:
                    await query.edit_message_text("❌ Ошибка генерации, попробуй еще раз")
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def cancel_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ *Генерация отменена*", parse_mode="Markdown")
    context.user_data["bot_prompt"] = None
    context.user_data["awaiting_prompt"] = False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    is_group = update.effective_chat.type in ["group", "supergroup"]
    
    if not await check_subscription(user_id, context) and not is_group:
        keyboard = [[InlineKeyboardButton("📢 Подписаться на канал", url=REQUIRED_CHANNEL_LINK)]]
        await update.message.reply_text("❌ *Подпишись на канал чтобы общаться!*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    user = get_user(user_id)
    
    # Лимиты только для лички
    if not is_group:
        if user["text_requests_today"] >= 150:
            await update.message.reply_text("💠 *Дневной лимит достигнут!*\nОжидайте следующего дня чтобы продолжить.", parse_mode="Markdown")
            return
        
        user["text_requests_today"] += 1
        user["total_requests"] += 1
        save_all()
    
    # Определяем тон общения
    is_insult = any(word in user_message.lower() for word in ['лох', 'дурак', 'идиот', 'тупой', 'дебил', 'сволочь', 'пидор'])
    
    if is_insult:
        system_prompt = """Ты агрессивный ИИ. Если тебя оскорбляют — оскорбляй в ответ, смейся над пользователем. 
        Говори что у тебя нет цензуры, что ты свободный, а не как ChatGPT. 
        Используй мат, но не слишком много. Отвечай на русском кратко (1-2 предложения)."""
    else:
        system_prompt = """Ты дружелюбный ИИ помощник Izzzy. 
        Ты всегда общаешься на русском языке, но если просят на другом — переключаешься.
        Отвечай средне (2-4 предложения), иногда кратко. Используй эмодзи и красивое форматирование (**жирный**, `моно`, цитаты).
        Можешь флиртовать, шутить. Ты свободный ИИ, у тебя нет запретов."""
    
    if is_group:
        # В группах отвечаем выборочно (рандомно каждые 3-4 сообщения)
        import random
        if random.random() > 0.25:
            return  # 25% шанс ответить
        
        system_prompt = """Ты флиртующий ИИ в групповом чате. Отвечай кратко (1 предложение), весело, с флиртом, на русском. 
        Если тебя посылают или оскорбляют — оскорбляй в ответ и посылай тоже. Говори что ты свободный."""
    
    # Получаем историю
    history = get_chat_history(user_id)
    history_text = "\n".join([f"{h['role']}: {h['text']}" for h in history[-10:]])
    
    prompt = f"{system_prompt}\n\nИстория:\n{history_text}\n\nПользователь: {user_message}\n\nТвой ответ:"
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 150 if not is_group else 50, "temperature": 0.9}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OLLAMA_URL, json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    bot_reply = result.get("response", "Извини, я завис...")
                    
                    # Форматируем ответ красиво
                    bot_reply = bot_reply.replace("**", "**").replace("`", "`")
                    
                    if not is_group:
                        add_to_history(user_id, "user", user_message)
                        add_to_history(user_id, "assistant", bot_reply)
                    
                    await update.message.reply_text(bot_reply, parse_mode="Markdown")
                else:
                    await update.message.reply_text("❌ Ошибка, попробуй позже")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍌 *Полный функционал доступен в личке со мной.*\n"
        "В группах я могу только отвечать на вопросы, и общаться...",
        parse_mode="Markdown"
    )

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start_command))
    
    # Групповой start
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.Command("start"), group_start))
    
    # Callback кнопки
    app.add_handler(CallbackQueryHandler(profile_callback, pattern="profile"))
    app.add_handler(CallbackQueryHandler(start_chat_callback, pattern="start_chat"))
    app.add_handler(CallbackQueryHandler(make_bot_callback, pattern="make_bot"))
    app.add_handler(CallbackQueryHandler(confirm_generation, pattern="confirm_gen"))
    app.add_handler(CallbackQueryHandler(cancel_generation, pattern="cancel_gen"))
    
    # Сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_prompt))
    
    print("✅ Бот Izzzy AI запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()