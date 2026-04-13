import asyncio
import sqlite3
import random
import re
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

# pip install g4f Pillow
import g4f
from PIL import Image
import io
import base64

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8710524054:AAEW493gKKIRUCTcFF3yXeNiUxCW17qB-D4"
CHANNEL_ID = -1003851572008
CHANNEL_URL = "https://t.me/izzzy_vpn"
DEV_USERNAME = "@parvizwp"

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect("izzy_bot.db")
    cur = conn.cursor()
    
    # Таблица пользователей
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица запросов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            request_type TEXT,
            prompt TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # Таблица истории чатов (для контекста в группах)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            user_id INTEGER,
            message TEXT,
            role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

def save_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    conn = sqlite3.connect("izzy_bot.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def save_request(user_id: int, request_type: str, prompt: str, result: str = None):
    conn = sqlite3.connect("izzy_bot.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO requests (user_id, request_type, prompt, result)
        VALUES (?, ?, ?, ?)
    """, (user_id, request_type, prompt, result))
    conn.commit()
    conn.close()

def get_user_requests(user_id: int, limit: int = 30):
    conn = sqlite3.connect("izzy_bot.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT request_type, prompt, created_at FROM requests
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows

def save_chat_message(chat_id: int, user_id: int, message: str, role: str = "user"):
    conn = sqlite3.connect("izzy_bot.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO chat_history (chat_id, user_id, message, role)
        VALUES (?, ?, ?, ?)
    """, (chat_id, user_id, message, role))
    conn.commit()
    conn.close()

def get_chat_context(chat_id: int, limit: int = 10):
    conn = sqlite3.connect("izzy_bot.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, message, role FROM chat_history
        WHERE chat_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (chat_id, limit))
    rows = cur.fetchall()
    conn.close()
    return list(reversed(rows))

# Счётчик сообщений для рандомных ответов бота в группах
group_message_counter = {}

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎨 Генерировать картинку")],
            [KeyboardButton(text="📄 Извлечь текст")],
            [KeyboardButton(text="📋 Мои запросы")],
        ],
        resize_keyboard=True
    )
    return kb

def get_channel_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Подписаться на канал", url=CHANNEL_URL)
    kb.button(text="✅ Проверить подписку", callback_data="check_sub")
    kb.adjust(1)
    return kb.as_markup()

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def check_subscription(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status not in ["left", "kicked", "banned"]
    except:
        return False

# ========== ИИ ФУНКЦИИ ==========
async def generate_image(prompt: str) -> Optional[bytes]:
    """Генерация картинки через g4f"""
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            provider=g4f.Provider.BingCreateImages,
            messages=[{"role": "user", "content": prompt}],
        )
        
        if isinstance(response, str) and response.startswith("http"):
            import requests
            img_response = requests.get(response)
            return img_response.content
        return None
    except Exception as e:
        print(f"Image generation error: {e}")
        
        # Fallback: пробуем другой провайдер
        try:
            response = g4f.ChatCompletion.create(
                model=g4f.models.gpt_4o,
                provider=g4f.Provider.PollinationsAI,
                messages=[{"role": "user", "content": f"Generate image: {prompt}"}],
            )
            return None
        except:
            return None

async def extract_text_from_image(image_data: bytes, instruction: str = "") -> str:
    """Извлечение текста из картинки через g4f с vision"""
    try:
        # Конвертируем в base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        prompt = instruction if instruction else "Извлеки весь текст с этого изображения. Верни только текст, без комментариев."
        
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4o,
            provider=g4f.Provider.PollinationsAI,
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\n![image](data:image/jpeg;base64,{image_base64})"
            }],
        )
        return response
    except Exception as e:
        print(f"Text extraction error: {e}")
        try:
            # Fallback
            response = g4f.ChatCompletion.create(
                model=g4f.models.gpt_4o,
                provider=g4f.Provider.Liaobots,
                messages=[{
                    "role": "user",
                    "content": [{"type": "text", "text": instruction or "Что написано на этой картинке?"},
                               {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}]
                }],
            )
            return response
        except:
            return "Не удалось распознать текст на изображении."

async def chat_response(message: str, context: list = None) -> str:
    """Ответ бота в чате"""
    try:
        messages = [{"role": "system", "content": "Ты Izzzy AI — дружелюбный помощник. Отвечай кратко, с лёгким юмором и флиртом, как человек. Используй эмодзи. Не будь роботом. Иногда кокетничай."}]
        
        if context:
            for ctx in context[-5:]:
                role = "assistant" if ctx[2] == "bot" else "user"
                messages.append({"role": role, "content": ctx[1]})
        
        messages.append({"role": "user", "content": message})
        
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4o,
            provider=g4f.Provider.PollinationsAI,
            messages=messages,
        )
        return response
    except:
        try:
            response = g4f.ChatCompletion.create(
                model="gpt-3.5-turbo",
                provider=g4f.Provider.Liaobots,
                messages=[{"role": "user", "content": message}],
            )
            return response
        except:
            return "😅 Что-то я задумалась... Повтори вопрос?"

# ========== БОТ И ДИСПЕТЧЕР ==========
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ========== СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ ==========
user_states = {}  # user_id: {"action": "generate_image" или "extract_text"}

# ========== ХЕНДЛЕРЫ ==========

# ----- КОМАНДЫ -----
@dp.message(CommandStart())
async def start_cmd(message: Message):
    user = message.from_user
    save_user(user.id, user.username, user.first_name, user.last_name)
    
    # В ЛИЧКЕ
    if message.chat.type == ChatType.PRIVATE:
        is_sub = await check_subscription(bot, user.id)
        
        if not is_sub:
            await message.answer(
                "⚠️ Для использования бота необходимо подписаться на канал:\n"
                f"{CHANNEL_URL}\n\n"
                "После подписки нажмите кнопку проверки.",
                reply_markup=get_channel_keyboard()
            )
            return
        
        await message.answer(
            "🍁 Добро пожаловать в Izzzy AI - твой бесплатный помощник, который всегда под рукой. "
            "Я умею писать тексты, генерировать картинки, и многое другое, ознакомиться можно по кнопкам ниже",
            reply_markup=get_main_keyboard()
        )
    
    # В ГРУППЕ
    else:
        await message.answer(
            "💠 В чатах я могу иногда общаться с пользователями, полный функционал доступен только в личных сообщениях со мной."
        )

@dp.message(Command("help"))
async def help_cmd(message: Message):
    help_text = (
        "🍁 Я Izzzy AI - ваш бесплатный помощник который всегда рядом с вами.\n\n"
        "- Я умею генерировать текст и общаться в чатах, группах\n"
        "- Умею генерировать картинки\n"
        "- Извлекать текст из фото\n\n"
        f"🗨️ Мой функционал ещё маленький, но меня улучшают каждый день и добавляют новые функции\n\n"
        f"👨‍💻 Разработчик: {DEV_USERNAME}"
    )
    await message.reply(help_text)

# ----- ПРОВЕРКА ПОДПИСКИ (CALLBACK) -----
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_sub = await check_subscription(bot, user_id)
    
    if is_sub:
        await callback.message.delete()
        await callback.message.answer(
            "✅ Подписка подтверждена! Добро пожаловать!\n\n"
            "🍁 Я Izzzy AI - твой бесплатный помощник, который всегда под рукой.",
            reply_markup=get_main_keyboard()
        )
        await callback.answer("✅ Доступ открыт!")
    else:
        await callback.answer("❌ Вы ещё не подписаны на канал!", show_alert=True)

# ----- КНОПКИ МЕНЮ -----
@dp.message(F.text == "🎨 Генерировать картинку")
async def generate_image_btn(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        await message.reply("🎨 Генерация картинок доступна только в личных сообщениях. Напиши мне в ЛС!")
        return
    
    is_sub = await check_subscription(bot, message.from_user.id)
    if not is_sub:
        await message.answer("⚠️ Подпишитесь на канал!", reply_markup=get_channel_keyboard())
        return
    
    user_states[message.from_user.id] = {"action": "generate_image"}
    await message.answer(
        "🗨️ Киньте текст описав, что хотите на картинке, например:\n"
        "Кот прыгает с самолёта"
    )

@dp.message(F.text == "📄 Извлечь текст")
async def extract_text_btn(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        await message.reply("📄 Извлечение текста доступно только в личных сообщениях. Напиши мне в ЛС!")
        return
    
    is_sub = await check_subscription(bot, message.from_user.id)
    if not is_sub:
        await message.answer("⚠️ Подпишитесь на канал!", reply_markup=get_channel_keyboard())
        return
    
    user_states[message.from_user.id] = {"action": "extract_text"}
    await message.answer(
        "🍁 Теперь киньте пожалуйста фотографию с текстом описав, что мне сделать с ним."
    )

@dp.message(F.text == "📋 Мои запросы")
async def my_requests_btn(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        await message.reply("📋 История запросов доступна только в личных сообщениях.")
        return
    
    is_sub = await check_subscription(bot, message.from_user.id)
    if not is_sub:
        await message.answer("⚠️ Подпишитесь на канал!", reply_markup=get_channel_keyboard())
        return
    
    requests = get_user_requests(message.from_user.id, 30)
    
    if not requests:
        await message.answer("📋 У вас пока нет запросов.")
        return
    
    text = "📋 <b>Ваши последние запросы:</b>\n\n"
    for i, (req_type, prompt, created_at) in enumerate(requests, 1):
        short_prompt = prompt[:50] + "..." if len(prompt) > 50 else prompt
        text += f"{i}. [{req_type}] {short_prompt}\n   📅 {created_at[:16]}\n\n"
    
    await message.answer(text)

# ----- ОБРАБОТКА В ЛИЧКЕ -----
@dp.message(F.chat.type == ChatType.PRIVATE)
async def private_handler(message: Message):
    user_id = message.from_user.id
    
    # Проверка подписки
    is_sub = await check_subscription(bot, user_id)
    if not is_sub:
        await message.answer("⚠️ Подпишитесь на канал для использования бота!", reply_markup=get_channel_keyboard())
        return
    
    state = user_states.get(user_id, {})
    action = state.get("action")
    
    # ГЕНЕРАЦИЯ КАРТИНКИ
    if action == "generate_image":
        if not message.text:
            await message.answer("❌ Отправьте текстовое описание картинки.")
            return
        
        prompt = message.text
        save_request(user_id, "generate_image", prompt)
        
        wait_msg = await message.answer("⚡ Подождите пару секунд, идёт процесс генерации...")
        
        image_data = await generate_image(prompt)
        
        await wait_msg.delete()
        
        if image_data:
            caption = f"✅ Готова\n🇳🇵 Наш канал: {CHANNEL_URL}"
            await message.answer_photo(types.BufferedInputFile(image_data, filename="generated.jpg"), caption=caption)
            save_request(user_id, "generate_image", prompt, "success")
        else:
            await message.answer("❌ Не удалось сгенерировать изображение. Попробуйте другой запрос.")
            save_request(user_id, "generate_image", prompt, "failed")
        
        user_states.pop(user_id, None)
    
    # ИЗВЛЕЧЕНИЕ ТЕКСТА
    elif action == "extract_text":
        if not message.photo:
            if message.text:
                await message.answer("💠 Фотография не обнаружена...")
            else:
                await message.answer("📷 Отправьте фотографию с текстом.")
            return
        
        # Есть фото
        instruction = message.caption or ""
        
        if not instruction:
            await message.answer("⚠️ Фотография обнаружена, без текста я не смогу выполнить...")
            return
        
        wait_msg = await message.answer("⚡ Выполняю запрос, подождите пару секунд....")
        
        # Скачиваем фото
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        image_data = await bot.download_file(file.file_path)
        
        result = await extract_text_from_image(image_data.read(), instruction)
        
        await wait_msg.delete()
        await message.answer(f"📄 <b>Результат:</b>\n\n{result}")
        
        save_request(user_id, "extract_text", instruction, result[:500] if result else None)
        user_states.pop(user_id, None)
    
    # ОБЫЧНОЕ СООБЩЕНИЕ
    else:
        # Просто общаемся с ИИ
        wait_msg = await message.answer("⚡ Думаю...")
        response = await chat_response(message.text)
        await wait_msg.delete()
        await message.answer(response)
        save_request(user_id, "chat", message.text, response[:500])

# ----- ОБРАБОТКА В ГРУППАХ -----
@dp.message(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]))
async def group_handler(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text or message.caption or ""
    
    if not text:
        return
    
    # Сохраняем сообщение
    save_chat_message(chat_id, user_id, text, "user")
    
    # Считаем сообщения для рандомных ответов
    group_message_counter[chat_id] = group_message_counter.get(chat_id, 0) + 1
    
    # Проверяем, обращаются ли к боту
    bot_names = ["иззи", "еззи", "izzzy", "izzy", "изи", "бот"]
    text_lower = text.lower()
    
    mentioned = any(name in text_lower for name in bot_names)
    has_question = "?" in text
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.id
    
    should_respond = False
    
    if mentioned or has_question or is_reply_to_bot:
        should_respond = True
    elif group_message_counter[chat_id] % random.randint(3, 5) == 0:
        # Рандомный ответ раз в 3-5 сообщений
        should_respond = True
    
    if should_respond:
        # Получаем контекст
        context = get_chat_context(chat_id, 10)
        
        # Определяем стиль ответа
        styles = ["friendly", "flirty", "funny"]
        style = random.choice(styles)
        
        style_prompt = {
            "friendly": "Ответь дружелюбно и кратко.",
            "flirty": "Ответь с лёгким флиртом и кокетством, как девушка или парень.",
            "funny": "Ответь с юмором, коротко и смешно."
        }
        
        full_prompt = f"{style_prompt[style]}\n\nСообщение: {text}"
        response = await chat_response(full_prompt, context)
        
        await asyncio.sleep(random.uniform(0.5, 2.0))
        await message.reply(response)
        
        save_chat_message(chat_id, bot.id, response, "bot")
        
        # Иногда генерируем картинку в тему
        if random.random() < 0.1:  # 10% шанс
            try:
                img_prompt = f"Сгенерируй картинку в тему обсуждения: {text[:200]}"
                image_data = await generate_image(img_prompt)
                if image_data:
                    await asyncio.sleep(1)
                    await message.reply_photo(
                        types.BufferedInputFile(image_data, filename="chat_image.jpg"),
                        caption="🎨 Сгенерировала картиночку в тему беседы 😊"
                    )
            except:
                pass

# ========== ЗАПУСК ==========
async def main():
    print("🍁 Izzzy AI запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())