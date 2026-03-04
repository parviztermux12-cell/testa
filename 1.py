import telebot
import requests
import random
import time
import re
from telebot import types
from bs4 import BeautifulSoup
import urllib.parse

# Токен бота (замени на свой)
TOKEN = '8259575977:AAHwfVOSF058L-bMan1l6NanOZUNsPrw7D0'
bot = telebot.TeleBot(TOKEN)

# Список поисковых запросов для реалистичных аниме-изображений
# Используются безопасные, художественные запросы
SEARCH_QUERIES = [
    "аниме арт реалистичная голая жопа",
    "реалистичное аниме концепт арт",
    "аниме девушка рвут жопу",
    "realistic anime girl digital art",
    "anime character realistic drawing",
    "фотография в стиле аниме девушка",
    "anime style realistic portrait",
    "3d аниме девушка в трусах",
    "realistic anime fan art girl",
    "аниме девушка с членом в жопе"
]

# Функция для поиска изображений в Яндекс.Картинках
def search_yandex_images(query, limit=10):
    """Поиск изображений в Яндекс.Картинках"""
    images = []
    try:
        # Кодируем запрос для URL
        encoded_query = urllib.parse.quote(query)
        
        # Формируем URL для поиска
        url = f"https://yandex.ru/images/search?text={encoded_query}&isize=large"
        
        # Заголовки как у реального браузера
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://yandex.ru/'
        }
        
        # Отправляем запрос
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем все изображения в результатах
            img_tags = soup.find_all('img', {'class': 'serp-item__thumb'})
            
            for img in img_tags[:limit]:
                if img.get('src'):
                    img_url = 'https:' + img['src']
                    images.append(img_url)
                elif img.get('data-src'):
                    img_url = 'https:' + img['data-src']
                    images.append(img_url)
                    
    except Exception as e:
        print(f"Ошибка поиска: {e}")
    
    return images

# Функция для скачивания изображения
def download_image(url):
    """Скачивает изображение по URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.content
    except:
        pass
    return None

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Создаем клавиатуру с кнопкой
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🎨 Получить изображение")
    markup.add(btn1)
    
    welcome_text = (
        "🌸 *Аниме Арт Бот* 🌸\n\n"
        "Привет! Я ищу красивые реалистичные аниме-изображения "
        "в Яндекс.Картинках.\n\n"
        "Нажми кнопку ниже, чтобы получить случайное изображение!"
    )
    
    bot.send_message(message.chat.id, welcome_text, 
                    parse_mode='Markdown', reply_markup=markup)

# Обработка нажатия на кнопку
@bot.message_handler(func=lambda message: message.text == "🎨 Получить изображение")
def handle_button(message):
    bot.send_message(message.chat.id, "🔍 Ищу красивое изображение... Подожди немного.")
    
    # Выбираем случайный запрос
    query = random.choice(SEARCH_QUERIES)
    
    # Ищем изображения
    images = search_yandex_images(query, limit=15)
    
    if images:
        # Выбираем случайное изображение из найденных
        img_url = random.choice(images)
        
        # Скачиваем его
        img_data = download_image(img_url)
        
        if img_data:
            # Отправляем фото
            bot.send_photo(
                message.chat.id, 
                img_data,
                caption=f"🔍 Запрос: {query}\n✨ Наслаждайся!"
            )
        else:
            # Если не удалось скачать, пробуем еще раз
            handle_button(message)
    else:
        bot.send_message(
            message.chat.id, 
            "😕 Не удалось найти изображения. Попробуй еще раз!"
        )

# Команда для поиска по своему запросу
@bot.message_handler(commands=['search'])
def cmd_search(message):
    msg = bot.send_message(
        message.chat.id,
        "Введи поисковый запрос (например: 'аниме арт реализм'):"
    )
    bot.register_next_step_handler(msg, process_custom_search)

def process_custom_search(message):
    query = message.text
    
    if len(query) < 3:
        bot.send_message(message.chat.id, "Слишком короткий запрос. Попробуй еще раз.")
        return
    
    bot.send_message(message.chat.id, f"🔍 Ищу по запросу: {query}")
    
    images = search_yandex_images(query, limit=10)
    
    if images:
        img_url = random.choice(images)
        img_data = download_image(img_url)
        
        if img_data:
            bot.send_photo(
                message.chat.id,
                img_data,
                caption=f"🔍 Поиск: {query}"
            )
        else:
            bot.send_message(message.chat.id, "Не удалось загрузить изображение. Попробуй другой запрос.")
    else:
        bot.send_message(message.chat.id, "Ничего не найдено. Попробуй другой запрос.")

# Команда помощи
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📖 *Как пользоваться ботом:*\n\n"
        "• Нажми кнопку '🎨 Получить изображение' для случайного арта\n"
        "• Используй /search для поиска по своему запросу\n"
        "• /help - это сообщение\n\n"
        "Бот ищет изображения в Яндекс.Картинках по запросам "
        "связанным с реалистичным аниме-стилем."
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# Запуск бота
if __name__ == '__main__':
    print("🌸 Аниме Арт Бот запущен...")
    print("Нажми Ctrl+C для остановки")
    
    # Устанавливаем более надежный polling
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)