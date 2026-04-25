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

TELEGRAM_TOKEN = "8627616199:AAGPsQ0XvQQFT0CpdWFoLNVnOcWJ254h_jA"
GEMINI_API_KEY = "AIzaSyA9p8L5nA_P3il7tiAupDHkNez0WEDKXfs"

# Настройка Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
vision_model = genai.GenerativeModel('gemini-2.5-flash')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
chats = {}

# Хранилище настроек пользователей
user_settings = {}

# ===== ГЛАВНОЕ МЕНЮ С КНОПКАМИ =====
def main_menu():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        KeyboardButton("/help"),
        KeyboardButton("/currency"),
        KeyboardButton("/news"),
        KeyboardButton("/start")
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

# ===== ФУНКЦИЯ КУРСОВ ВАЛЮТ (BYN) =====
def get_exchange_rates():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        usd_byn = data['rates'].get('BYN', 'Нет данных')
        eur_byn = data['rates'].get('BYN', 'Нет данных') * (data['rates'].get('EUR', 1) / data['rates'].get('USD', 1))
        usd_rub = data['rates'].get('RUB', 'Нет данных')
        
        text = f"""
💵 **Курсы валют (USD → BYN):** {usd_byn:.2f} Br
💶 **Курсы валют (EUR → BYN):** {eur_byn:.2f} Br

📋 **Для справки:**
💵 USD → RUB: {usd_rub:.2f} ₽

📅 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        return text
    except Exception as e:
        return f"❌ Ошибка получения курсов: {e}"

# ===== ФУНКЦИЯ НОВОСТЕЙ =====
def get_news():
    try:
        news_sites = [
            {"name": "РИА Новости", "url": "https://ria.ru/lenta/"},
            {"name": "ТАСС", "url": "https://tass.ru/"},
            {"name": "Ведомости", "url": "https://www.vedomosti.ru/"}
        ]
        
        text = "📰 **Последние новости:**\n\n"
        for site in news_sites:
            text += f"• [{site['name']}]({site['url']})\n"
        
        text += "\n🔍 Напиши /news [тема] для поиска новостей по теме"
        return text
    except Exception as e:
        return f"❌ Ошибка получения новостей: {e}"

def search_news(topic):
    try:
        prompt = f"Дай 3 свежих новости на тему '{topic}'. Напиши кратко, с источниками."
        response = model.generate_content(prompt)
        return f"📰 **Новости по теме '{topic}':**\n\n{response.text}"
    except Exception as e:
        return f"❌ Ошибка: {e}"

# ===== ФУНКЦИЯ WIKIPEDIA =====
def search_wikipedia(query):
    try:
        url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{query}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', query)
            extract = data.get('extract', 'Нет описания')
            page_url = data.get('content_urls', {}).get('desktop', {}).get('page', '')
            
            text = f"📖 **{title}**\n\n{extract[:500]}"
            if page_url:
                text += f"\n\n🔗 [Читать полностью]({page_url})"
            return text
        else:
            prompt = f"Расскажи кратко о '{query}' как в Wikipedia"
            response = model.generate_content(prompt)
            return f"📖 **{query}**\n\n{response.text[:500]}..."
    except Exception as e:
        return f"❌ Ошибка Wikipedia: {e}"

# ===== ВЫБОР ЯЗЫКА =====
def set_language(user_id, lang):
    user_settings[user_id] = {'language': lang}
    return f"🌐 Язык изменен на {lang}"

def get_language(user_id):
    return user_settings.get(user_id, {}).get('language', 'ru')

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
        
        prompt = "Извлеки весь текст с этого изображения. Если текста нет, напиши 'Текст не найден'"
        
        file_type = mimetypes.guess_type(file_url)[0] or 'image/jpeg'
        
        response_vision = vision_model.generate_content([
            prompt,
            {
                "mime_type": file_type,
                "data": base64.b64encode(image_bytes).decode('utf-8')
            }
        ])
        
        extracted_text = response_vision.text
        bot.edit_message_text(f"✅ **Текст:**\n{extracted_text}", user_id, msg.message_id, parse_mode='Markdown')
        
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)[:200]}", user_id, msg.message_id)

# ===== КОМАНДЫ =====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    chats[user_id] = model.start_chat(history=[])
    user_settings[user_id] = {'language': 'ru'}
    
    help_text = """
🌟 **Добро пожаловать в Gemini Бот!** 🌟

📷 **Распознавание текста с фото**
   - Отправь любое фото с текстом

🌤 **Погода:** /weather [город]
   Пример: /weather Минск

💵 **Курсы валют:** /currency

📰 **Новости:** /news или /news [тема]

📖 **Wikipedia:** /wiki [запрос]

🌐 **Сменить язык:** /language [ru/en]

💬 **Просто напиши вопрос** - отвечу!

📌 Используй кнопки внизу для быстрого доступа!
    """
    bot.send_message(user_id, help_text, parse_mode='Markdown', reply_markup=main_menu())

# ===== ОБРАБОТЧИК HELP =====
@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = message.chat.id
    
    help_text = """
🌟 **Доступные команды:** 🌟

📷 **Распознавание текста**
   • Отправь фото с текстом

🌤 **Погода**
   • /weather Минск - погода в городе

💵 **Курсы валют**
   • /currency - USD/BYN, EUR/BYN

📰 **Новости**
   • /news - главные новости
   • /news технологии - новости по теме

📖 **Wikipedia**
   • /wiki Минск - информация из Википедии

🌐 **Язык ответов**
   • /language ru - русский
   • /language en - английский

💬 **Просто напиши вопрос** - отвечу!

📌 Кнопки внизу отправляют команды автоматически!
    """
    bot.send_message(user_id, help_text, parse_mode='Markdown', reply_markup=main_menu())

@bot.message_handler(commands=['weather'])
def weather_command(message):
    city = message.text.replace('/weather', '').strip()
    if not city:
        bot.reply_to(message, "🌤 Укажи город!\nПример: `/weather Минск`", parse_mode='Markdown')
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    weather_info = get_weather(city)
    bot.reply_to(message, weather_info, parse_mode='Markdown')

@bot.message_handler(commands=['currency'])
def currency_command(message):
    bot.send_chat_action(message.chat.id, 'typing')
    rates = get_exchange_rates()
    bot.reply_to(message, rates, parse_mode='Markdown')

@bot.message_handler(commands=['news'])
def news_command(message):
    topic = message.text.replace('/news', '').strip()
    
    if topic:
        bot.send_chat_action(message.chat.id, 'typing')
        news_info = search_news(topic)
    else:
        bot.send_chat_action(message.chat.id, 'typing')
        news_info = get_news()
    
    bot.reply_to(message, news_info, parse_mode='Markdown', disable_web_page_preview=True)

@bot.message_handler(commands=['wiki'])
def wiki_command(message):
    query = message.text.replace('/wiki', '').strip()
    if not query:
        bot.reply_to(message, "📖 Укажи запрос!\nПример: `/wiki Минск`", parse_mode='Markdown')
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    wiki_info = search_wikipedia(query)
    bot.reply_to(message, wiki_info, parse_mode='Markdown', disable_web_page_preview=True)

@bot.message_handler(commands=['language'])
def language_command(message):
    user_id = message.chat.id
    lang = message.text.replace('/language', '').strip().lower()
    
    if lang not in ['ru', 'en']:
        bot.reply_to(message, "🌐 Доступные языки: `ru` или `en`\nПример: `/language en`", parse_mode='Markdown')
        return
    
    result = set_language(user_id, lang)
    bot.reply_to(message, result, parse_mode='Markdown')

# ===== ОСНОВНОЙ ОБРАБОТЧИК =====
@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = message.chat.id
    user_text = message.text
    
    if user_id not in chats:
        chats[user_id] = model.start_chat(history=[])
    
    # Добавляем информацию о языке в промпт
    lang = get_language(user_id)
    if lang == 'en':
        user_text = f"[Answer in English] {user_text}"
    
    try:
        bot.send_chat_action(user_id, 'typing')
        response = chats[user_id].send_message(user_text)
        bot.send_message(user_id, response.text[:4096])
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка: {str(e)[:150]}")

# ===== ЗАПУСК =====
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 БОТ ЗАПУЩЕН!")
    print("=" * 50)
    print("✅ Кнопки отправляют команды:")
    print("   /help     - Помощь")
    print("   /currency - Курсы валют")
    print("   /news     - Новости")
    print("   /start    - Главное меню")
    print("=" * 50)
    bot.polling(none_stop=True)
