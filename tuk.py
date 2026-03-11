#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
from telebot import types
import torch
from diffusers import StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler
import io
import time
import threading
import random
import os
from PIL import Image
import gc

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = '8259575977:AAGBvgNlwpcQV7s3qer3tHqJb-Ajvos4qTQ'  # Твой токен
bot = telebot.TeleBot(TOKEN)

# Глобальная переменная для модели
pipe = None
model_loaded = False
generation_queue = []

# Модель для генерации реалистичных аниме-девушек
MODEL_ID = "John6666/mala-anime-mix-nsfw-pony-xl-v3-sdxl"

# ========== ЗАГРУЗКА МОДЕЛИ ==========
def load_model():
    """Загружает модель в память"""
    global pipe, model_loaded
    
    try:
        print("🚀 Загрузка модели... Это займет 2-3 минуты")
        
        # Используем GPU если доступен
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32
        
        # Загружаем модель
        pipe = StableDiffusionXLPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=dtype,
            safety_checker=None,  # Отключаем цензуру для 18+
            requires_safety_checker=False,
            variant="fp16" if device == "cuda" else None
        )
        
        pipe.to(device)
        
        # Оптимизация для скорости
        if device == "cuda":
            pipe.enable_xformers_memory_efficient_attention()
            pipe.enable_model_cpu_offload()  # Экономия VRAM
        
        # Настройка сэмплера для лучшего качества
        pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
        
        model_loaded = True
        print("✅ Модель загружена и готова к работе!")
        
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        model_loaded = False

# ========== ФУНКЦИЯ ГЕНЕРАЦИИ ==========
def generate_image(prompt, negative_prompt=None):
    """Генерирует изображение по промпту"""
    global pipe
    
    if pipe is None:
        return None
    
    try:
        # Стандартные негативные промпты для качества
        if negative_prompt is None:
            negative_prompt = (
                "lowres, bad anatomy, bad hands, text, error, missing fingers, "
                "extra digit, fewer digits, cropped, worst quality, low quality, "
                "normal quality, jpeg artifacts, signature, watermark, username, blurry, "
                "bad proportions, gross, ugly, bad face, bad eyes"
            )
        
        # Улучшаем промпт для реалистичных аниме-девушек
        enhanced_prompt = f"{prompt}, realistic anime style, beautiful face, perfect eyes, detailed face, professional, highly detailed, 8k, photorealistic, masterpiece, best quality"
        
        # Параметры генерации
        width = 768
        height = 1152  # Вертикальный формат как на фото
        
        with torch.no_grad():
            image = pipe(
                prompt=enhanced_prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=30,  # Качество генерации
                guidance_scale=7.5,  # Насколько строго следовать промпту
                num_images_per_prompt=1
            ).images[0]
        
        return image
        
    except Exception as e:
        print(f"Ошибка генерации: {e}")
        return None

# ========== КОМАНДЫ БОТА ==========

@bot.message_handler(commands=['start'])
def start_command(message):
    """Приветственное сообщение"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🎨 Сгенерировать")
    btn2 = types.KeyboardButton("❓ Помощь")
    markup.add(btn1, btn2)
    
    welcome_text = (
        "🌸 **Аниме Генератор** 🌸\n\n"
        "Привет! Я создаю красивых аниме-девушек по твоему описанию.\n\n"
        "Просто напиши описание или нажми кнопку!\n"
        "Примеры:\n"
        "• девушка с длинными розовыми волосами\n"
        "• готическая лолита, черные волосы\n"
        "• школьница, очки, косички\n"
        "• киберпанк, неоновые огни"
    )
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "📖 **Как пользоваться:**\n\n"
        "1. Напиши описание девушки\n"
        "2. Бот сгенерирует изображение\n\n"
        "**Советы по описанию:**\n"
        "• Указывай цвет волос, глаз\n"
        "• Добавляй детали: одежда, фон\n"
        "• Можно указывать позу или эмоцию\n\n"
        "**Примеры:**\n"
        "`девушка с длинными серебристыми волосами, фиолетовые глаза, кимоно, сакура`\n"
        "`блондинка, голубые глаза, улыбается, школьная форма, солнечный день`"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Обработка текстовых сообщений"""
    global model_loaded
    
    # Проверка нажатия кнопок
    if message.text == "🎨 Сгенерировать":
        msg = bot.send_message(message.chat.id, "✏️ Напиши описание девушки:")
        bot.register_next_step_handler(msg, generate_handler)
        return
    
    if message.text == "❓ Помощь":
        help_command(message)
        return
    
    # Если просто текст - генерируем
    generate_handler(message)

def generate_handler(message):
    """Обработчик генерации"""
    global model_loaded
    
    prompt = message.text
    
    # Проверяем длину
    if len(prompt) < 3:
        bot.send_message(message.chat.id, "❌ Слишком короткое описание. Напиши подробнее!")
        return
    
    # Проверяем загрузку модели
    if not model_loaded:
        bot.send_message(message.chat.id, "⏳ Модель еще загружается... Подожди 1-2 минуты и попробуй снова.")
        return
    
    # Отправляем статус
    status_msg = bot.send_message(
        message.chat.id, 
        f"🎨 Генерирую: *{prompt}*\n⏳ Это займет 20-30 секунд...",
        parse_mode='Markdown'
    )
    
    try:
        # Генерируем изображение
        image = generate_image(prompt)
        
        if image:
            # Сохраняем в байтовый поток
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG', quality=95)
            img_bytes.seek(0)
            
            # Создаем клавиатуру для регенерации
            markup = types.InlineKeyboardMarkup()
            regen_btn = types.InlineKeyboardButton(
                "🔄 Сгенерировать заново", 
                callback_data=f"regen_{prompt[:50]}"  # Обрезаем длинный промпт
            )
            markup.add(regen_btn)
            
            # Удаляем статусное сообщение
            bot.delete_message(message.chat.id, status_msg.message_id)
            
            # Отправляем фото
            bot.send_photo(
                message.chat.id,
                img_bytes,
                caption=f"✨ Результат по запросу:\n*{prompt}*",
                parse_mode='Markdown',
                reply_markup=markup
            )
            
            # Очищаем память
            del image
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
        else:
            bot.edit_message_text(
                "❌ Ошибка генерации. Попробуй другое описание.",
                message.chat.id,
                status_msg.message_id
            )
            
    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка: {str(e)[:100]}",
            message.chat.id,
            status_msg.message_id
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('regen_'))
def regenerate_callback(call):
    """Обработка кнопки регенерации"""
    prompt = call.data[5:]  # Убираем 'regen_'
    
    # Отвечаем на callback
    bot.answer_callback_query(call.id, "🔄 Генерирую заново...")
    
    # Создаем статусное сообщение
    status_msg = bot.send_message(
        call.message.chat.id,
        f"🔄 Регенерация: *{prompt}*...",
        parse_mode='Markdown'
    )
    
    try:
        # Генерируем новое изображение
        image = generate_image(prompt)
        
        if image:
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Клавиатура для новой регенерации
            markup = types.InlineKeyboardMarkup()
            regen_btn = types.InlineKeyboardButton(
                "🔄 Сгенерировать заново", 
                callback_data=f"regen_{prompt[:50]}"
            )
            markup.add(regen_btn)
            
            # Удаляем статус
            bot.delete_message(call.message.chat.id, status_msg.message_id)
            
            # Отправляем новое фото
            bot.send_photo(
                call.message.chat.id,
                img_bytes,
                caption=f"✨ Регенерация:\n*{prompt}*",
                parse_mode='Markdown',
                reply_markup=markup
            )
            
            # Очищаем память
            del image
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
        else:
            bot.edit_message_text(
                "❌ Ошибка при регенерации",
                call.message.chat.id,
                status_msg.message_id
            )
            
    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка: {str(e)[:100]}",
            call.message.chat.id,
            status_msg.message_id
        )

# ========== ЗАПУСК ==========

if __name__ == '__main__':
    print("🌸 Запуск аниме-генератора...")
    
    # Загружаем модель в отдельном потоке
    threading.Thread(target=load_model).start()
    
    print("✅ Бот активен. Нажми Ctrl+C для остановки.")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"❌ Ошибка бота: {e}")
            time.sleep(3)