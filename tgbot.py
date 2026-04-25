#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Bot с интеграцией OpenAI API
Автор: Ваше Имя
GitHub: ссылка на репозиторий
"""

import telebot
import requests
import logging
import sys
from typing import Optional

# Пытаемся импортировать конфиг
try:
    import config
except ImportError:
    print("❌ Ошибка: файл config.py не найден!")
    print("Скопируйте config.example.py в config.py и добавьте свои токены")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpenAIBot:
    """Класс для работы с Telegram ботом и OpenAI API"""
    
    def __init__(self):
        """Инициализация бота"""
        self.bot = telebot.TeleBot(config.TELEGRAM_TOKEN)
        self._register_handlers()
        logger.info("Бот успешно инициализирован")
    
    def _register_handlers(self):
        """Регистрация обработчиков команд"""
        self.bot.message_handler(commands=['start'])(self.send_welcome)
        self.bot.message_handler(commands=['help'])(self.send_help)
        self.bot.message_handler(commands=['reset'])(self.reset_chat)
        self.bot.message_handler(func=lambda message: True)(self.handle_message)
    
    def ask_openai(self, question: str) -> Optional[str]:
        """
        Отправка запроса к OpenAI API
        
        Args:
            question: Текст вопроса пользователя
            
        Returns:
            Ответ от API или сообщение об ошибке
        """
        headers = {
            "Authorization": f"Bearer {config.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.MODEL,
            "messages": [
                {
                    "role": "system", 
                    "content": "Ты полезный ассистент. Отвечай на русском языке, подробно и по делу."
                },
                {"role": "user", "content": question}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                config.OPENAI_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                logger.info(f"Успешный ответ от API (длина: {len(answer)} символов)")
                return answer
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return f"❌ Ошибка API: {response.status_code}\nПроверьте API ключ и баланс"
                
        except requests.exceptions.Timeout:
            logger.error("Timeout при запросе к API")
            return "❌ Превышено время ожидания ответа от сервера"
        except requests.exceptions.ConnectionError:
            logger.error("Connection error при запросе к API")
            return "❌ Не удалось подключиться к API. Проверьте интернет"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"❌ Неожиданная ошибка: {str(e)}"
    
    def send_welcome(self, message):
        """Обработчик команды /start"""
        welcome_text = """
🤖 **Привет! Я бот с искусственным интеллектом**

Я использую нейросеть OpenAI, чтобы отвечать на ваши вопросы.

**Что я умею:**
• Отвечать на любые вопросы
• Помогать с кодом
• Объяснять сложные темы
• Переводить текст

**Команды:**
/start - Показать это сообщение
/help - Подробная справка
/reset - Очистить диалог

Просто напишите мне любой вопрос!
"""
        self.bot.reply_to(message, welcome_text, parse_mode='Markdown')
    
    def send_help(self, message):
        """Обработчик команды /help"""
        help_text = """
📚 **Справка по использованию**

**Как задавать вопросы:**
• Пишите на любом языке (лучше на русском)
• Чем точнее вопрос, тем точнее ответ
• Можно задавать уточняющие вопросы

**Примеры вопросов:**
• "Какой класс у Buick Invicta 2024 года?"
• "Напиши код калькулятора на Python"
• "Объясни теорему Пифагора"
• "Переведи на английский: привет мир"

**Ограничения:**
• Максимальная длина ответа - 1000 токенов (~750 слов)
• Если ответ слишком длинный, он разобьется на части

**Техническая информация:**
• Модель: {model}
• API: OpenAI
• Бот написан на Python

По всем вопросам: @ваш_телеграм
""".format(model=config.MODEL)
        self.bot.reply_to(message, help_text, parse_mode='Markdown')
    
    def reset_chat(self, message):
        """Обработчик команды /reset"""
        self.bot.reply_to(message, "🔄 Контекст диалога очищен! Задавайте новый вопрос.")
    
    def handle_message(self, message):
        """Обработка всех текстовых сообщений"""
        user_question = message.text
        
        # Пропускаем команды
        if user_question.startswith('/'):
            return
        
        # Индикатор печати
        self.bot.send_chat_action(message.chat.id, 'typing')
        
        # Получаем ответ
        answer = self.ask_openai(user_question)
        
        # Отправляем ответ (с разбивкой если нужно)
        if answer and len(answer) > 4096:
            for i in range(0, len(answer), 4096):
                self.bot.reply_to(message, answer[i:i+4096])
        else:
            self.bot.reply_to(message, answer)
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск бота...")
        print(f"\n{'='*50}")
        print(f"🤖 Бот запущен!")
        print(f"📱 Telegram: @{self.bot.get_me().username}")
        print(f"🧠 Модель: {config.MODEL}")
        print(f"🔗 API URL: {config.OPENAI_API_URL}")
        print(f"{'='*50}\n")
        
        try:
            self.bot.infinity_polling(timeout=60)
        except KeyboardInterrupt:
            print("\n👋 Бот остановлен пользователем")
            logger.info("Бот остановлен")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            sys.exit(1)


if __name__ == "__main__":
    bot = OpenAIBot()
    bot.run()
