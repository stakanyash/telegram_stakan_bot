import logging
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from datetime import datetime, timedelta
import json

with open('config.json', 'r') as file:
    config = json.load(file)

TOKEN = config["TOKEN"]
SOURCE_CHAT_ID = config["SOURCE_CHAT_ID"]
DESTINATION_CHAT_ID = config["DESTINATION_CHAT_ID"]
ALLOWED_USER_IDS = config["ALLOWED_USER_IDS"]

# Log creation
log_filename = f"bot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variable to store errors and warnings
errors_and_warnings = []

class CustomHandler(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.WARNING:
            errors_and_warnings.append(self.format(record))

# Add custom handler to the logger
logger.addHandler(CustomHandler())

def handle_exceptions(func):
    async def wrapper(update: Update, context):
        try:
            await func(update, context)
        except Exception as e:
            logger.error(f"Exception in command {func.__name__}: {e}")
            raise
    return wrapper

@handle_exceptions
async def start(update: Update, context) -> None:
    await update.message.reply_text('Приветствую. Данный бот пересылает сообщения из канала @stakanyasher в отдельный чат и не работает в других чатах или каналах.')

@handle_exceptions
async def test(update: Update, context) -> None:
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username
    chat_id = str(update.message.chat.id)

    if user_id in ALLOWED_USER_IDS or chat_id in ALLOWED_USER_IDS:
        logger.info(f"Command /test received from allowed user/chat {user_id}/{chat_id}")
        await update.message.reply_text('Спокуха, я живой')
    else:
        logger.warning(f"Command /test attempted by unauthorized user {username}")

@handle_exceptions
async def admintest(update: Update, context) -> None:
    user_id = str(update.message.from_user.id)
    chat_id = str(update.message.chat.id)

    if user_id in ALLOWED_USER_IDS or chat_id in ALLOWED_USER_IDS:
        logger.info(f"Command /admintest received from allowed user/chat {user_id}/{chat_id}")
        if errors_and_warnings:
            response = "\n".join(errors_and_warnings)
            logger.info("Errors and warnings reported:")
            logger.info(response)
        else:
            response = "За сессию работы бота не было ошибок или предупреждений"
            logger.info("No errors or warnings reported.")
        await update.message.reply_text(response)
    else:
        logger.warning(f"Command /admintest attempted by unauthorized user {user_id}")

@handle_exceptions
async def raise_error(update: Update, context) -> None:
    user_id = str(update.message.from_user.id)
    chat_id = str(update.message.chat.id)

    if user_id in ALLOWED_USER_IDS or chat_id in ALLOWED_USER_IDS:
        logger.info(f"Command /raiseerror received from allowed user/chat {user_id}/{chat_id}")
        # Intentionally raise an exception for testing
        raise Exception("This is a test exception")
    else:
        logger.warning(f"Command /raiseerror attempted by unauthorized user {user_id}")

@handle_exceptions
async def forward_message(update: Update, context) -> None:
    if update.channel_post and update.channel_post.chat.id == int(SOURCE_CHAT_ID):
        message_id = update.channel_post.message_id
        logger.info(f"Forwarding message from {update.channel_post.chat.id} to {DESTINATION_CHAT_ID} with message ID {message_id}")
        try:
            await context.bot.copy_message(chat_id=DESTINATION_CHAT_ID, from_chat_id=update.channel_post.chat.id, message_id=message_id)
        except Exception as e:
            logger.error(f"Failed to forward message: {e}")

def main() -> None:
    logger.info("Starting bot...")
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test))
    application.add_handler(CommandHandler("admintest", admintest))
    application.add_handler(CommandHandler("raiseerror", raise_error))
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, forward_message))

    application.run_polling()

if __name__ == '__main__':
    main()
