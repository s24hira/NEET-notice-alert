import telebot
import logging
from functools import wraps

class BotHandlers:
    def __init__(self, bot, storage):
        self.bot = bot
        self.storage = storage
        self.setup_commands()

    def ensure_user(self, func):
        @wraps(func)
        def wrapper(message):
            user_id = message.chat.id
            username = message.from_user.username
            if self.storage.add_user(user_id, username):
                logging.info(f"New user {user_id} added from {func.__name__}.")
            return func(message)
        return wrapper

    def setup_commands(self):
        @self.bot.message_handler(commands=['start'])
        @self.ensure_user
        def start_command(message):
            start_msg = "Welcome! You'll now receive NEET notice alerts!"
            self.bot.reply_to(message, start_msg)

        @self.bot.message_handler(commands=['status'])
        @self.ensure_user
        def status_command(message):
            status_msg = "Bot Status: ✅ Running"
            self.bot.reply_to(message, status_msg)

        @self.bot.message_handler(commands=['help'])
        @self.ensure_user
        def help_command(message):
            help_text = """
            NEET Notice Bot Commands:
            /start - Begin receiving notice alerts
            /status - Check current bot status
            /help - Display this help message
            """
            self.bot.reply_to(message, help_text)