import telebot
import google.generativeai as genai
import requests
from PIL import Image
from io import BytesIO

TELEGRAM_TOKEN = "8627616199:AAGPsQ0XvQQFT0CpdWFoLNVnOcWJ254h_jA"
GEMINI_API_KEY = "AIzaSyA9p8L5nA_P3il7tiAupDHkNez0WEDKXfs"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
vision_model = genai.GenerativeModel('gemini-2.5-flash')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
chats = {}

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    msg = bot.send_message(user_id, "📷 Обрабатываю фото...")
    try:
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
        response = requests.get(file_url)
        img = Image.open(BytesIO(response.content))
        prompt = "Извлеки весь текст с этого изображения"
        response_vision = vision_model.generate_content([prompt, img])
        bot.edit_message_text(f"✅ Текст: {response_vision.text}", user_id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {e}", user_id, msg.message_id)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    chats[user_id] = model.start_chat(history=[])
    bot.send_message(user_id, "🌟 Бот готов! Отправь фото для распознавания текста")

@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = message.chat.id
    if user_id not in chats:
        chats[user_id] = model.start_chat(history=[])
    response = chats[user_id].send_message(message.text)
    bot.send_message(user_id, response.text[:4096])

bot.polling(none_stop=True)
