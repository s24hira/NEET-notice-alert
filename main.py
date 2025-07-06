import os
import random
import logging
import telebot
import schedule
import time
from dotenv import load_dotenv
from flask import Flask, jsonify
import threading

# Import modular components
from bot.storage import SupabaseStorage
from bot.handlers import BotHandlers
from bot.notice_processor import NoticeProcessor
from bot.utils.summarizer import GeminiPDFSummarizer

# Configure logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout # Output logs to console
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
NEET_WEBSITE_URL = os.getenv('NEET_WEBSITE_URL', 'https://neet.nta.nic.in/')

# Ensure data directory exists
os.makedirs('data', exist_ok=True)
os.makedirs('data/temp', exist_ok=True)

class NEETNoticeBot:
    def __init__(self):
        self.bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
        self.storage = SupabaseStorage()
        self.summarizer = GeminiPDFSummarizer(GEMINI_API_KEY)
        self.notice_processor = NoticeProcessor(self.summarizer, self.storage, NEET_WEBSITE_URL)
        self.handlers = BotHandlers(self.bot, self.storage)

    def reset_webhook(self):
        """Reset any existing webhook to ensure clean polling"""
        try:
            self.bot.delete_webhook()
            time.sleep(0.5)  # Wait for webhook deletion to complete
            logger.info("Webhook reset successful")
        except Exception as e:
            logger.error(f"Error resetting webhook: {e}")

    def run(self):
        def scheduled_job():
            try:
                self.notice_processor.process_new_notices(self.bot)
            except Exception as e:
                logger.error(f"Error in scheduled job: {e}")
            
            next_interval = random.randint(300, 480)  # 5-8 minutes
            schedule.clear('notice_check')
            schedule.every(next_interval).seconds.do(scheduled_job).tag('notice_check')
            logger.info(f"Next check scheduled in {next_interval} seconds")

        try:
            self.reset_webhook()
            
            logger.info("Starting initial notice check")
            scheduled_job()

            # Start Telegram bot polling in a separate thread
            polling_thread = threading.Thread(target=self.bot.polling, kwargs={'none_stop': True, 'timeout': 30, 'long_polling_timeout': 90})
            polling_thread.daemon = True
            polling_thread.start()
            logger.info("Bot polling started in separate thread")

            # Start a simple HTTP server for health checks in a separate thread
            def run_health_check_server():
                app = Flask(__name__)

                @app.route('/health', methods=['GET'])
                def health_check():
                    return jsonify({'status': 'ok'}), 200

                PORT = int(os.getenv('HEALTH_CHECK_PORT', 8001))
                # Use a production-ready WSGI server like waitress or gunicorn
                # For simplicity, we'll use Flask's built-in server here,
                # but it's not recommended for production.
                app.run(host='0.0.0.0', port=PORT)

            health_check_thread = threading.Thread(target=run_health_check_server)
            health_check_thread.daemon = True
            health_check_thread.start()
            logger.info("Health check server started in separate thread")


            logger.info("Starting main scheduler loop")
            while True:
                schedule.run_pending()
                time.sleep(1)

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise

def main():
    logger.info("Starting NEET Notice Bot application...")
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY environment variable not set")
        return
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'):
        logger.error("Supabase URL or Key not set in environment variables.")
        return
        
    bot = NEETNoticeBot()
    bot.run()

if __name__ == '__main__':
    main()