import telebot
import google.generativeai as genai
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TELEGRAM_TOKEN = "8627616199:AAGPsQ0XvQQFT0CpdWFoLNVnOcWJ254h_jA"
GEMINI_API_KEY = "AIzaSyA9p8L5nA_P3il7tiAupDHkNez0WEDKXfs"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
chats = {}

# ===== ГЛАВНОЕ МЕНЮ С КНОПКАМИ =====
def main_menu():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        KeyboardButton("ℹ️ Помощь"),
        KeyboardButton("🔄 Новый диалог"),
        KeyboardButton("⭐ О боте")
    ]
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    chats[user_id] = model.start_chat(history=[])
    
    bot.send_message(
        user_id, 
        "🌟 **Добро пожаловать в Gemini Бот!**\n\n"
        "Просто напиши сообщение - я отвечу!\n\n"
        "Используй кнопки ниже 👇",
        parse_mode='Markdown',
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🤖 **Команды бота:**

/start - Перезапустить бота
/help - Показать помощь

**Кнопки:**
• ℹ️ Помощь - показать команды
• 🔄 Новый диалог - начать заново
• ⭐ О боте - информация

**Как пользоваться:**
Просто напиши сообщение - я отвечу!
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown', reply_markup=main_menu())

# ===== ОБРАБОТКА ТЕКСТОВЫХ КНОПОК =====
@bot.message_handler(func=lambda message: message.text == "ℹ️ Помощь")
def help_button(message):
    help_command(message)

@bot.message_handler(func=lambda message: message.text == "🔄 Новый диалог")
def new_chat_button(message):
    user_id = message.chat.id
    chats[user_id] = model.start_chat(history=[])
    bot.send_message(user_id, "🔄 **Новый диалог начат!** Можешь задавать вопросы.", parse_mode='Markdown', reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "⭐ О боте")
def about_button(message):
    about_text = """
⭐ **О боте**

🤖 **Версия:** 1.0
🧠 **Модель:** Gemini 2.5 Flash
👨‍💻 **Создан:** на Python с Telebot

**Особенности:** 
• Запоминает контекст диалога
• Быстрые и умные ответы
• Простые кнопки

Просто напиши сообщение - я отвечу!
    """
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown', reply_markup=main_menu())

# ===== ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ =====
@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = message.chat.id
    user_text = message.text
    
    # Пропускаем команды-кнопки
    if user_text in ["ℹ️ Помощь", "🔄 Новый диалог", "⭐ О боте"]:
        return
    
    if user_id not in chats:
        chats[user_id] = model.start_chat(history=[])
    
    try:
        bot.send_chat_action(user_id, 'typing')
        response = chats[user_id].send_message(user_text)
        bot.send_message(user_id, response.text[:4096])
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка: {str(e)[:150]}", reply_markup=main_menu())

# ===== ЗАПУСК =====
if __name__ == '__main__':
    print("=" * 40)
    print("🚀 GEMINI БОТ ЗАПУЩЕН!")
    print("=" * 40)
    print("✅ Модель: Gemini 2.5 Flash")
    print("✅ Кнопки: Помощь, Новый диалог, О боте")
    print("=" * 40)
    bot.polling(none_stop=True)