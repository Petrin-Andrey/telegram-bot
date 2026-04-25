import telebot
import requests
import json
import logging
from typing import Optional

# ========== НАСТРОЙКИ ==========
# Токен вашего Telegram-бота (получить у @BotFather)
TELEGRAM_TOKEN = "8627616199:AAGPsQ0XvQQFT0CpdWFoLNVnOcWJ254h_jA"

# Ключ API OpenAI (получить на platform.openai.com)
OPENAI_API_KEY = "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"

# Какую модель использовать
MODEL = "https://api-inference.huggingface.co/models/IlyaGusev/saiga_mistral_7b_gguf"  # или "gpt-4"

# URL API OpenAI (ПРАВИЛЬНЫЙ эндпоинт)
OPENAI_API_URL = "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"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ========== ФУНКЦИЯ ЗАПРОСА К OPENAI ==========
def ask_openai(question: str) -> Optional[str]:
    """
    Отправляет запрос к OpenAI API и возвращает ответ.
    Использует POST-запрос с JSON-телом (НЕ GET с параметром msg).
    """
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Ты полезный ассистент, отвечающий на русском языке."},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        # ПРАВИЛЬНО: POST-запрос с JSON
        response = requests.post(
            OPENAI_API_URL,
            headers=headers,
            json=payload,  # автоматически сериализует в JSON
            timeout=30
        )
        
        # Проверяем статус
        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            return answer
        else:
            logger.error(f"API error {response.status_code}: {response.text}")
            return f"Ошибка API: {response.status_code}\n{response.text}"
            
    except requests.exceptions.Timeout:
        return "Ошибка: превышено время ожидания ответа от API"
    except requests.exceptions.ConnectionError:
        return "Ошибка: не удалось подключиться к API"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Неожиданная ошибка: {str(e)}"

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветственное сообщение при /start"""
    bot.reply_to(
        message,
        "👋 Привет! Я бот на основе OpenAI.\n\n"
        "Просто напиши мне любой вопрос, и я постараюсь ответить.\n\n"
        "Доступные команды:\n"
        "/start - показать это сообщение\n"
        "/help - справка\n"
        "/reset - очистить историю диалога"
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    """Справка"""
    bot.reply_to(
        message,
        "📚 **Справка**\n\n"
        "• Задавайте любые вопросы текстом\n"
        "• Бот отвечает на русском языке\n"
        "• Используется модель " + MODEL + "\n\n"
        "Примеры вопросов:\n"
        "- Какой класс у Buick Invicta 2024?\n"
        "- Что такое ассемблер?\n"
        "- 2 + 2 * 2 = ?"
    )

@bot.message_handler(commands=['reset'])
def reset_chat(message):
    """Сброс контекста (простой вариант - просто приветствие)"""
    bot.reply_to(message, "🔄 Контекст диалога очищен! Задавайте новый вопрос.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """
    Обработка всех текстовых сообщений.
    Отправляет вопрос в OpenAI и возвращает ответ.
    """
    user_question = message.text
    
    # Отправляем "печатает..." для индикации
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Получаем ответ от OpenAI
    answer = ask_openai(user_question)
    
    # Отправляем ответ пользователю
    if answer and len(answer) > 4096:
        # Если ответ слишком длинный, разбиваем на части
        for i in range(0, len(answer), 4096):
            bot.reply_to(message, answer[i:i+4096])
    else:
        bot.reply_to(message, answer)

# ========== ЗАПУСК БОТА ==========
if __name__ == "__main__":
    print("🤖 Бот запущен...")
    print(f"Используется модель: {MODEL}")
    print(f"API URL: {OPENAI_API_URL}")
    print("Нажмите Ctrl+C для остановки")
    
    try:
        bot.infinity_polling(timeout=60)
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
