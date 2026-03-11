import telebot
import requests
import base64
import os
import time
from telebot import types

# ТВОЙ ТОКЕН
TOKEN = '8259575977:AAGBvgNlwpcQV7s3qer3tHqJb-Ajvos4qTQ'
bot = telebot.TeleBot(TOKEN)

# ТВОЙ API КЛЮЧ STABILITY AI
STABILITY_KEY = 'sk-Qhm76aPAhqB5mEVMuIJB63EVIQSGTIzxusILuHUfMgInDyJi'

# Папка для сохранения
OUTPUT_DIR = "./generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_image(prompt):
    """Генерирует изображение через Stability AI"""
    try:
        # Улучшаем промпт для качества
        enhanced_prompt = f"{prompt}, masterpiece, best quality, highly detailed, 4k"
        
        # Запрос к Stability AI
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/ultra",
            headers={
                "Authorization": f"Bearer {STABILITY_KEY}",
                "Accept": "image/*"
            },
            files={"none": ""},
            data={
                "prompt": enhanced_prompt,
                "aspect_ratio": "9:16",  # Вертикальный формат как на фото
                "output_format": "png"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            # Сохраняем изображение
            filename = f"{OUTPUT_DIR}/img_{int(time.time())}.png"
            with open(filename, "wb") as f:
                f.write(response.content)
            return filename
        else:
            print(f"Ошибка API: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Ошибка генерации: {e}")
        return None

@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start"""
    welcome_text = (
        "🎨 **Stability AI Генератор**\n\n"
        "Привет! Просто напиши любой промт, и я сгенерирую изображение.\n\n"
        "Примеры:\n"
        "• `аниме девушка, длинные розовые волосы`\n"
        "• `реалистичный портрет девушки, голубые глаза`\n"
        "• `девушку в аниме стиле, которую ебут в жопу большим членом`\n\n"
        "✏️ Отправь свой промт:"
    )
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_prompt(message):
    """Обработка любого текстового сообщения"""
    prompt = message.text
    
    # Отправляем статус
    status_msg = bot.reply_to(
        message,
        f"🎨 Генерирую: *{prompt[:100]}*...\n⏳ Подожди 20-30 секунд",
        parse_mode='Markdown'
    )
    
    try:
        # Генерируем изображение
        image_path = generate_image(prompt)
        
        if image_path and os.path.exists(image_path):
            # Отправляем фото
            with open(image_path, 'rb') as photo:
                bot.send_photo(
                    message.chat.id,
                    photo,
                    caption=f"✅ Готово!\n📝 *{prompt[:200]}*",
                    parse_mode='Markdown'
                )
            
            # Удаляем файл
            os.remove(image_path)
            
            # Удаляем статусное сообщение
            bot.delete_message(message.chat.id, status_msg.message_id)
            
        else:
            bot.edit_message_text(
                "❌ Ошибка генерации. Попробуй другой промт.",
                message.chat.id,
                status_msg.message_id
            )
            
    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка: {str(e)[:100]}",
            message.chat.id,
            status_msg.message_id
        )

if __name__ == '__main__':
    print("🚀 Бот запущен...")
    print(f"📊 API Key: {'Установлен' if STABILITY_KEY else 'НЕТ'}")
    
    if not STABILITY_KEY:
        print("❌ Нет API ключа Stability AI!")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Ошибка бота: {e}")
            time.sleep(3)