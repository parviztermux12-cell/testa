import telebot
import os
import subprocess
import time
import shutil
from PIL import Image

# Токен бота
BOT_TOKEN = '8259575977:AAHwfVOSF058L-bMan1l6NanOZUNsPrw7D0'
bot = telebot.TeleBot(BOT_TOKEN)

# Папки
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

# Пути для клонирования с GitHub (автоматически создадутся)
REALESRGAN_PATH = os.path.join(BASE_DIR, 'Real-ESRGAN')
VIDEO2X_PATH = os.path.join(BASE_DIR, 'video2x')
UPSCAYL_PATH = os.path.join(BASE_DIR, 'upscayl')

user_settings = {}

# Функция установки Real-ESRGAN
def install_realesrgan():
    if not os.path.exists(REALESRGAN_PATH):
        os.system(f'git clone https://github.com/xinntao/Real-ESRGAN.git {REALESRGAN_PATH}')
        os.system(f'cd {REALESRGAN_PATH} && pip install -r requirements.txt')
        return "✅ Real-ESRGAN установлен"
    return "✅ Real-ESRGAN уже есть"

# Функция установки Video2X
def install_video2x():
    if not os.path.exists(VIDEO2X_PATH):
        os.system(f'git clone https://github.com/k4yt3x/video2x.git {VIDEO2X_PATH}')
        os.system(f'cd {VIDEO2X_PATH} && pip install -r requirements.txt')
        return "✅ Video2X установлен"
    return "✅ Video2X уже есть"

# Функция установки Upscayl
def install_upscayl():
    if not os.path.exists(UPSCAYL_PATH):
        os.system(f'git clone https://github.com/upscayl/upscayl.git {UPSCAYL_PATH}')
        os.system(f'cd {UPSCAYL_PATH} && npm install')
        return "✅ Upscayl установлен"
    return "✅ Upscayl уже есть"

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🎨 Real-ESRGAN', '🎬 Video2X', '📸 Upscayl')
    markup.add('📥 Установить все', '❓ Помощь')
    
    bot.send_message(
        message.chat.id,
        "👋 Отправь фото или видео для улучшения!\n\n"
        "Выбери инструмент снизу 👇",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == '📥 Установить все')
def install_all(message):
    msg = bot.send_message(message.chat.id, "⏳ Устанавливаю проекты с GitHub...")
    
    result = ""
    result += install_realesrgan() + "\n"
    result += install_video2x() + "\n"
    result += install_upscayl() + "\n"
    
    bot.edit_message_text(f"✅ Готово!\n{result}", message.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: m.text in ['🎨 Real-ESRGAN', '🎬 Video2X', '📸 Upscayl'])
def select_tool(message):
    tool = message.text.split(' ')[1]  # Real-ESRGAN, Video2X или Upscayl
    user_settings[message.from_user.id] = tool
    bot.send_message(message.chat.id, f"✅ Выбран {tool}. Теперь отправь файл!")

@bot.message_handler(func=lambda m: m.text == '❓ Помощь')
def help_msg(message):
    help_text = """
📖 **Как пользоваться:**

1. Нажми "📥 Установить все" (1 раз)
2. Выбери инструмент:
   🎨 Real-ESRGAN - фото/видео до 4K
   🎬 Video2X - повышение FPS видео
   📸 Upscayl - быстрое фото
3. Отправь файл
4. Получи результат

✅ Проекты сами скачаются с GitHub!
    """
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    tool = user_settings.get(user_id, 'Real-ESRGAN')
    
    status = bot.send_message(message.chat.id, f"⏳ Обрабатываю фото через {tool}...")
    
    # Скачиваем фото
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded = bot.download_file(file_info.file_path)
    
    # Сохраняем
    timestamp = int(time.time())
    input_path = os.path.join(TEMP_DIR, f"input_{user_id}_{timestamp}.jpg")
    output_path = os.path.join(TEMP_DIR, f"output_{user_id}_{timestamp}.jpg")
    
    with open(input_path, 'wb') as f:
        f.write(downloaded)
    
    try:
        if tool == 'Real-ESRGAN':
            # Real-ESRGAN команда
            cmd = f'cd {REALESRGAN_PATH} && python inference_realesrgan.py -i "{input_path}" -o "{output_path}" -n RealESRGAN_x4plus'
            os.system(cmd)
            
        elif tool == 'Upscayl':
            # Upscayl команда
            cmd = f'cd {UPSCAYL_PATH} && node src/cli.js -i "{input_path}" -o "{output_path}" -s 4'
            os.system(cmd)
        
        # Отправляем результат
        if os.path.exists(output_path):
            with open(output_path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption=f"✅ Готово! (через {tool})")
            bot.delete_message(message.chat.id, status.message_id)
        else:
            bot.send_message(message.chat.id, "❌ Ошибка обработки")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")
    
    # Чистим
    for p in [input_path, output_path]:
        if os.path.exists(p):
            os.remove(p)

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id
    tool = user_settings.get(user_id, 'Real-ESRGAN')
    
    status = bot.send_message(message.chat.id, f"⏳ Обрабатываю видео через {tool}... Это может занять время")
    
    # Скачиваем видео
    file_info = bot.get_file(message.video.file_id)
    downloaded = bot.download_file(file_info.file_path)
    
    timestamp = int(time.time())
    input_path = os.path.join(TEMP_DIR, f"input_{user_id}_{timestamp}.mp4")
    output_path = os.path.join(TEMP_DIR, f"output_{user_id}_{timestamp}.mp4")
    
    with open(input_path, 'wb') as f:
        f.write(downloaded)
    
    try:
        if tool == 'Real-ESRGAN':
            # Для видео Real-ESRGAN обрабатывает каждый кадр
            frames_dir = os.path.join(TEMP_DIR, f"frames_{timestamp}")
            os.makedirs(frames_dir, exist_ok=True)
            
            # Извлекаем кадры
            os.system(f'ffmpeg -i "{input_path}" -q:v 1 "{frames_dir}/frame_%04d.jpg"')
            
            # Обрабатываем каждый кадр
            for frame in sorted(os.listdir(frames_dir)):
                frame_path = os.path.join(frames_dir, frame)
                out_frame = os.path.join(frames_dir, f"enhanced_{frame}")
                cmd = f'cd {REALESRGAN_PATH} && python inference_realesrgan.py -i "{frame_path}" -o "{out_frame}" -n RealESRGAN_x4plus'
                os.system(cmd)
            
            # Собираем видео обратно
            os.system(f'ffmpeg -r 30 -i "{frames_dir}/enhanced_frame_%04d.jpg" -i "{input_path}" -c:v libx264 -c:a aac "{output_path}"')
            
            # Чистим кадры
            shutil.rmtree(frames_dir)
            
        elif tool == 'Video2X':
            # Video2X команда
            cmd = f'cd {VIDEO2X_PATH} && python video2x.py -i "{input_path}" -o "{output_path}" -p realesrgan -sf 2'
            os.system(cmd)
        
        # Отправляем результат
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            with open(output_path, 'rb') as f:
                bot.send_video(message.chat.id, f, caption=f"✅ Готово! (через {tool})")
            bot.delete_message(message.chat.id, status.message_id)
        else:
            bot.send_message(message.chat.id, "❌ Ошибка обработки видео")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")
    
    # Чистим
    for p in [input_path, output_path]:
        if os.path.exists(p):
            os.remove(p)

# Запуск
if __name__ == '__main__':
    print("✅ Бот запущен!")
    print(f"📁 Проекты будут установлены в: {BASE_DIR}")
    print("\n📥 Нажми в боте 'Установить все' для скачивания с GitHub")
    bot.infinity_polling()