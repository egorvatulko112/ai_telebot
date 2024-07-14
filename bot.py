from telebot import TeleBot, types
import os
import google.generativeai as genai
import time
from threading import Thread

def configure_ai():
    genai.configure(api_key=os.environ["	"])
    return genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config={
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        },
        system_instruction="Тебя зовут Gemini, ты находишься в Telegram боте.",
    )

class TelegramBot:
    def __init__(self, token, model):
        self.bot = TeleBot(token)
        self.model = model
        self.user_last_message_time = {}
        self.setup_handlers()
        Thread(target=self.schedule_checks).start()

    def setup_handlers(self):
        self.bot.message_handler(commands=['start'])(self.start)
        self.bot.message_handler(content_types=['text'])(self.handle_text)
        self.bot.message_handler(func=lambda message: True,
                                 content_types=['photo', 'video', 'document', 'audio', 'voice', 'sticker', 'contact', 'location', 'venue'])(self.handle_non_text)

    def start(self, message):
        chat_id = message.chat.id
        self.user_last_message_time[chat_id] = time.time()
        self.bot.reply_to(message, 'Сессия чтения начата. Напишите мне что-нибудь в течение минуты.')

    def handle_text(self, message):
        chat_id = message.chat.id
        self.user_last_message_time[chat_id] = time.time()
        self.bot.send_chat_action(chat_id, 'typing')
        time.sleep(1)
        chat_session = self.model.start_chat(history=[])
        response = chat_session.send_message(message.text)
        self.bot.reply_to(message, response.text)

    def handle_non_text(self, message):
        self.bot.reply_to(message, 'Пожалуйста, напишите текстовой запрос, я пока умею обрабатывать только текст.')

    def end_chat_session(self, chat_id):
        self.user_last_message_time.pop(chat_id, None)
        self.bot.send_message(chat_id, 'Сессия завершена из-за отсутствия активности.')

    def check_user_activity(self):
        current_time = time.time()
        for chat_id, last_message_time in list(self.user_last_message_time.items()):
            if current_time - last_message_time > 60:
                self.end_chat_session(chat_id)

    def schedule_checks(self):
        while True:
            self.check_user_activity()
            time.sleep(1)

    def run(self):
        self.bot.polling()

if __name__ == '__main__':
    model = configure_ai()
    bot = TelegramBot(os.environ["TELEGRAM_BOT_TOKEN"], model)
    bot.run()
