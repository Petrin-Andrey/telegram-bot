import telebot
import google.generativeai as genai
import requests
from io import BytesIO
import json
import base64
import mimetypes
from datetime import datetime
import random
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ===== ТОКЕНЫ =====
TELEGRAM_TOKEN = "8627616199:AAGPsQ0XvQQFT0CpdWFoLNVnOcWJ254h_jA"
GEMINI_API_KEY = "AIzaSyA9p8L5nA_P3il7tiAupDHkNez0WEDKXfs"

# ===== НАСТРОЙКА GEMINI =====
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
vision_model = genai.GenerativeModel('gemini-2.5-flash')

# ===== ИНИЦИАЛИЗАЦИЯ БОТА =====
bot = telebot.TeleBot(TELEGRAM_TOKEN)
chats = {}
user_settings = {}

# ===== ГЛАВНОЕ МЕНЮ С КНОПКАМИ =====
def main_menu():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        KeyboardButton("ℹ️ Помощь"),
        KeyboardButton("🔄 Новый диалог"),
        KeyboardButton("⭐ О боте"),
        KeyboardButton("💵 Курс валют"),
        KeyboardButton("📰 Новости"),
        KeyboardButton("🌤 Погода"),
        KeyboardButton("📖 Wikipedia")
    ]
    keyboard.add(*buttons)
    return keyboard

# ===== ФУНКЦИЯ ПОГОДЫ =====
def get_weather(city):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t+%w&lang=ru"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            weather_data = response.text.strip()
            return f"🌤 **Погода в {city}:**\n{weather_data}"
        else:
            return f"❌ Не могу найти город '{city}'"
    except Exception as e:
        return f"❌ Ошибка погоды: {e}"

# ===== ФУНКЦИЯ КУРСОВ ВАЛЮТ =====
def get_exchange_rates():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        usd_byn = data['rates'].get('BYN', 'Нет данных')
        eur_byn = data['rates'].get('BYN', 'Нет данных') * (data['rates'].get('EUR', 1) / data['rates'].get('USD', 1))
        usd_rub = data['rates'].get('RUB', 'Нет данных')
        
        text = f"""
💵 **USD → BYN:** {usd_byn:.2f} Br
💶 **EUR → BYN:** {eur_byn:.2f} Br

📋 Для справки:
💵 USD → RUB: {usd_rub:.2f} ₽

📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        return text
    except Exception as e:
        return f"❌ Ошибка: {e}"

# ===== ФУНКЦИЯ НОВОСТЕЙ =====
def get_news():
    news_sites = [
        "РИА Новости - https://ria.ru/lenta/",
        "ТАСС - https://tass.ru/",
        "Ведомости - https://www.vedomosti.ru/"
    ]
    text = "📰 **Новости:**\n\n" + "\n".join(news_sites)
    text += "\n\n🔍 /news [тема] - поиск новостей"
    return text

def search_news(topic):
    try:
        prompt = f"Дай 3 свежих новости на тему '{topic}'"
        response = model.generate_content(prompt)
        return f"📰 **Новости по теме '{topic}':**\n\n{response.text}"
    except:
        return "❌ Ошибка поиска новостей"

# ===== ФУНКЦИЯ WIKIPEDIA =====
def search_wikipedia(query):
    try:
        url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{query}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', query)
            extract = data.get('extract', 'Нет описания')[:500]
            return f"📖 **{title}**\n\n{extract}"
        else:
            return f"❌ Не найдено: {query}"
    except Exception as e:
        return f"❌ Ошибка: {e}"

# ===== ОБРАБОТКА ФОТО =====
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    msg = bot.send_message(user_id, "📷 Обрабатываю фото...")
    try:
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
        
        response = requests.get(file_url)
        image_bytes = response.content
        
        prompt = "Извлеки текст с этого изображения"
        file_type = 'image/jpeg'
        
        response_vision = vision_model.generate_content([
            prompt,
            {"mime_type": file_type, "data": base64.b64encode(image_bytes).decode('utf-8')}
        ])
        
        bot.edit_message_text(f"✅ **Текст:**\n{response_vision.text}", user_id, msg.message_id, parse_mode='Markdown')
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)[:200]}", user_id, msg.message_id)

# ===== КОМАНДЫ =====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    chats[user_id] = model.start_chat(history=[])
    user_settings[user_id] = {'language': 'ru'}
    
    text = """
🌟 **Gemini Бот** 🌟

📷 Отправь фото - распознаю текст
💬 Напиши вопрос - отвечу

📌 Используй кнопки внизу!
    """
    bot.send_message(user_id, text, parse_mode='Markdown', reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def help_command(message):
    text = """
🌟 **Команды:**

/start - Главное меню
/help - Помощь
/weather [город] - Погода
/currency - Курсы валют
/news [тема] - Новости
/wiki [запрос] - Wikipedia

📌 Кнопки внизу работают без интернета!
    """
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu())

@bot.message_handler(commands=['weather'])
def weather_command(message):
    city = message.text.replace('/weather', '').strip()
    if not city:
        bot.reply_to(message, "🌤 Пример: `/weather Минск`", parse_mode='Markdown')
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, get_weather(city), parse_mode='Markdown')

@bot.message_handler(commands=['currency'])
def currency_command(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, get_exchange_rates(), parse_mode='Markdown')

@bot.message_handler(commands=['news'])
def news_command(message):
    topic = message.text.replace('/news', '').strip()
    
    if topic:
        bot.send_chat_action(message.chat.id, 'typing')
        bot.reply_to(message, search_news(topic), parse_mode='Markdown')
    else:
        bot.reply_to(message, get_news(), parse_mode='Markdown', disable_web_page_preview=True)

@bot.message_handler(commands=['wiki'])
def wiki_command(message):
    query = message.text.replace('/wiki', '').strip()
    if not query:
        bot.reply_to(message, "📖 Пример: `/wiki Минск`", parse_mode='Markdown')
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, search_wikipedia(query), parse_mode='Markdown')

# ===== ОБРАБОТЧИКИ КНОПОК (БЕЗ GEMINI) =====
@bot.message_handler(func=lambda message: message.text == "ℹ️ Помощь")
def help_button(message):
    help_command(message)

@bot.message_handler(func=lambda message: message.text == "🔄 Новый диалог")
def new_dialog_button(message):
    user_id = message.chat.id
    chats[user_id] = model.start_chat(history=[])
    bot.send_message(user_id, "✅ Новый диалог начат!", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "⭐ О боте")
def about_button(message):
    text = """
🤖 **О боте**

🧠 Модель: Gemini 2.5 Flash
💬 Поддержка контекста
📷 Распознавание текста с фото
🌤 Погода, курс валют, новости, Wikipedia

Создан на Python + Telebot
    """
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "💵 Курс валют")
def currency_button(message):
    currency_command(message)

@bot.message_handler(func=lambda message: message.text == "📰 Новости")
def news_button(message):
    news_command(message)

@bot.message_handler(func=lambda message: message.text == "🌤 Погода")
def weather_button(message):
    bot.send_message(message.chat.id, "🌤 Введите город после команды:\n`/weather Минск`", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "📖 Wikipedia")
def wiki_button(message):
    bot.send_message(message.chat.id, "📖 Введите запрос после команды:\n`/wiki Минск`", parse_mode='Markdown')

# ===== ОСНОВНОЙ ОБРАБОТЧИК (ТОЛЬКО ДЛЯ ТЕКСТА) =====
@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = message.chat.id
    user_text = message.text
    
    # Пропускаем текст кнопок, которые уже обработаны
    if user_text in ["ℹ️ Помощь", "🔄 Новый диалог", "⭐ О боте", "💵 Курс валют", "📰 Новости", "🌤 Погода", "📖 Wikipedia"]:
        return
    
    if user_id not in chats:
        chats[user_id] = model.start_chat(history=[])
    
    try:
        bot.send_chat_action(user_id, 'typing')
        response = chats[user_id].send_message(user_text)
        bot.send_message(user_id, response.text[:4096], reply_markup=main_menu())
    except Exception as e:
        if "429" in str(e):
            bot.send_message(user_id, "⚠️ Лимит запросов. Попробуйте позже или используйте кнопки меню.", reply_markup=main_menu())
        else:
            bot.send_message(user_id, f"❌ Ошибка: {str(e)[:150]}", reply_markup=main_menu())

# ===== ЗАПУСК =====
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 БОТ ЗАПУЩЕН!")
    print("=" * 50)
    print("✅ Кнопки работают без Gemini")
    print("✅ При ошибке 429 кнопки продолжают работать")
    print("=" * 50)
    bot.polling(none_stop=True)
