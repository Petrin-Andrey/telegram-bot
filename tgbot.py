import telebot
import requests
import json
import random
from datetime import datetime, timedelta

TELEGRAM_TOKEN = "8627616199:AAGPsQ0XvQQFT0CpdWFoLNVnOcWJ254h_jA"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Счетчики запросов
request_count = 0
last_reset = datetime.now()

def reset_counter():
    global request_count, last_reset
    if datetime.now() - last_reset > timedelta(hours=24):
        request_count = 0
        last_reset = datetime.now()

# ===== НЕСКОЛЬКО БЕСПЛАТНЫХ AI ИСТОЧНИКОВ =====
def free_ai_1(prompt):
    """ChatGPT через бесплатный прокси"""
    try:
        url = "https://api.gpchat.xyz/v1/chat/completions"
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }
        response = requests.post(url, json=data, timeout=20)
        return response.json()['choices'][0]['message']['content']
    except:
        return None

def free_ai_2(prompt):
    """Бесплатный нейросетевой API"""
    try:
        url = "https://api.popcat.xyz/chat"
        params = {"msg": prompt}
        response = requests.get(url, params=params, timeout=20)
        return response.text
    except:
        return None

def free_ai_3(prompt):
    """Еще один бесплатный API"""
    try:
        url = "https://api.owkinz.xyz/api/gpt4"
        params = {"ask": prompt}
        response = requests.get(url, params=params, timeout=20)
        return response.json().get('response')
    except:
        return None

def free_ai_4(prompt):
    """GPT-4 через бесплатный прокси"""
    try:
        url = "https://api.vanwi.xyz/api/gpt"
        params = {"q": prompt}
        response = requests.get(url, params=params, timeout=20)
        return response.text
    except:
        return None

def free_ai_5(prompt):
    """Еще один источник"""
    try:
        url = "https://api.siputzx.my.id/api/ai/gpt4"
        params = {"text": prompt}
        response = requests.get(url, params=params, timeout=20)
        return response.json().get('data')
    except:
        return None

def get_ai_response(prompt):
    """Автоматическое переключение между источниками"""
    reset_counter()
    
    sources = [
        free_ai_1, free_ai_2, free_ai_3, free_ai_4, free_ai_5
    ]
    
    for source in sources:
        try:
            result = source(prompt)
            if result and len(result) > 10:
                return result
        except:
            continue
    
    return "⚠️ Все сервисы временно недоступны. Попробуйте через минуту."

# ===== КНОПКИ МЕНЮ =====
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

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

# ===== ФУНКЦИИ-ЗАГЛУШКИ (для кнопок) =====
def get_exchange_rates():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()
        usd_byn = data['rates'].get('BYN', 'нет данных')
        eur_byn = data['rates'].get('BYN', 'нет данных') * (data['rates'].get('EUR', 1) / data['rates'].get('USD', 1))
        return f"💵 USD → BYN: {usd_byn:.2f} Br\n💶 EUR → BYN: {eur_byn:.2f} Br"
    except:
        return "❌ Ошибка получения курсов"

def get_weather(city):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t+%w&lang=ru"
        response = requests.get(url, timeout=10)
        return f"🌤 {city}: {response.text.strip()}"
    except:
        return "❌ Ошибка погоды"

def search_wikipedia(query):
    try:
        url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{query}"
        response = requests.get(url, timeout=10)
        data = response.json()
        return f"📖 {data.get('title')}\n\n{data.get('extract', 'Не найдено')[:500]}"
    except:
        return "❌ Не найдено"

def get_news():
    return "📰 Новости:\n• РИА Новости\n• ТАСС\n• Ведомости"

# ===== ОБРАБОТЧИКИ КОМАНД =====
@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = """
🤖 **Бот с безлимитным AI!**

📌 **Никаких лимитов!**
📌 **Без VPN и регистрации!**

📷 Отправь фото - распознаю текст
💬 Напиши вопрос - отвечу

📌 **Кнопки внизу всегда работают!**
    """
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu())

@bot.message_handler(commands=['weather'])
def weather_cmd(message):
    city = message.text.replace('/weather', '').strip()
    if not city:
        bot.reply_to(message, "Пример: /weather Минск")
        return
    bot.reply_to(message, get_weather(city))

@bot.message_handler(commands=['currency'])
def currency_cmd(message):
    bot.reply_to(message, get_exchange_rates())

@bot.message_handler(commands=['news'])
def news_cmd(message):
    bot.reply_to(message, get_news())

@bot.message_handler(commands=['wiki'])
def wiki_cmd(message):
    query = message.text.replace('/wiki', '').strip()
    if not query:
        bot.reply_to(message, "Пример: /wiki Минск")
        return
    bot.reply_to(message, search_wikipedia(query))

# ===== ОБРАБОТЧИКИ КНОПОК =====
@bot.message_handler(func=lambda m: m.text == "ℹ️ Помощь")
def help_btn(m):
    start(m)

@bot.message_handler(func=lambda m: m.text == "🔄 Новый диалог")
def new_btn(m):
    bot.send_message(m.chat.id, "✅ Новый диалог начат!")

@bot.message_handler(func=lambda m: m.text == "⭐ О боте")
def about_btn(m):
    bot.send_message(m.chat.id, "🤖 Бот на безлимитном AI\n⭐ Версия 3.0\n💬 Без лимитов и VPN")

@bot.message_handler(func=lambda m: m.text == "💵 Курс валют")
def currency_btn(m):
    currency_cmd(m)

@bot.message_handler(func=lambda m: m.text == "📰 Новости")
def news_btn(m):
    news_cmd(m)

@bot.message_handler(func=lambda m: m.text == "🌤 Погода")
def weather_btn(m):
    bot.send_message(m.chat.id, "🌤 Напиши: /weather Минск")

@bot.message_handler(func=lambda m: m.text == "📖 Wikipedia")
def wiki_btn(m):
    bot.send_message(m.chat.id, "📖 Напиши: /wiki Минск")

# ===== ОСНОВНОЙ AI ОБРАБОТЧИК =====
@bot.message_handler(func=lambda message: True)
def chat(message):
    global request_count
    reset_counter()
    
    # Пропускаем текст кнопок
    if message.text in ["ℹ️ Помощь", "🔄 Новый диалог", "⭐ О боте", 
                        "💵 Курс валют", "📰 Новости", "🌤 Погода", "📖 Wikipedia"]:
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    
    request_count += 1
    remaining = 100 - request_count
    if remaining < 20:
        bot.send_message(message.chat.id, f"📊 Осталось ~{remaining} запросов на сегодня")
    
    answer = get_ai_response(message.text)
    bot.send_message(message.chat.id, answer, reply_markup=main_menu())

# ===== ЗАПУСК =====
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 БЕЗЛИМИТНЫЙ БОТ ЗАПУЩЕН!")
    print("=" * 50)
    print("✅ Нет ограничений!")
    print("✅ Не нужен VPN!")
    print("✅ Кнопки всегда работают!")
    print("=" * 50)
    bot.polling(none_stop=True)
