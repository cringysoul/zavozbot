import logging
import os
import re
import random
import asyncio
import shutil
from dotenv import load_dotenv
from telegram import Update, ReactionTypeEmoji
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

import yt_dlp

# Исправление #6: logging и stdlib-импорты вверху, до сторонних библиотек
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Исправление #7: явная проверка токена при старте
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env")

# ID пользователя которому отвечаем гифкой
TARGET_USER_ID = 5002964279

# file_id гифок
GIF_FILES = [
    "CgACAgIAAxkBAAFD2mlpqH5Qrh_vFdkM_rbmUEJP3sJu6gAC3HYAAkciUEi9sy6F7yG9WToE",
    # Добавь сюда больше file_id гифок
]

REACTIONS = ["🔥", "👀", "🤡", "💯"]

message_counter = {}

def is_valid_url(text):
    pattern = r'(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com|instagram\.com/reel|twitter\.com|x\.com|youtube\.com|youtu\.be)'
    return bool(re.search(pattern, text))

def download_video(url: str):
    os.makedirs("downloads", exist_ok=True)
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        # Исправление #3: ограничение размера файла до 45 МБ (лимит Telegram — 50 МБ)
        'format': 'best[ext=mp4][filesize<45M]/best[filesize<45M]/best',
        'quiet': True,
        'merge_output_format': 'mp4',
        # Исправление #2: таймаут сокета — не зависаем вечно
        'socket_timeout': 30,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = f"downloads/{info['id']}.mp4"
        return filename

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.message.chat_id
    message_counter[chat_id] = message_counter.get(chat_id, 0) + 1
    if message_counter[chat_id] >= 150:
        message_counter[chat_id] = 0
        await update.message.reply_text("а я считаю это желтуха")
        # Исправление #1: убран return — если это ссылка, бот должен её обработать

    # Дальше работаем только с текстом
    if not update.message.text:
        return

    # Реакция на любое сообщение с шансом 7%
    if random.randint(1, 100) <= 7:
        try:
            await update.message.set_reaction(
                [ReactionTypeEmoji(emoji=random.choice(REACTIONS))]
            )
        except Exception as e:
            logger.warning(f"Не удалось поставить реакцию: {e}")

    # Исправление #5: reply_animation обёрнута в try/except
    if update.message.from_user and update.message.from_user.id == TARGET_USER_ID:
        if random.randint(1, 100) <= 5 and len(GIF_FILES) > 0:
            try:
                await update.message.reply_animation(
                    animation=random.choice(GIF_FILES),
                    reply_to_message_id=update.message.message_id
                )
            except Exception as e:
                logger.warning(f"Не удалось отправить гифку: {e}")

    text = update.message.text.strip()
    if not is_valid_url(text):
        return

    msg = await update.message.reply_text("⏳ Завозик...")
    filename = None
    try:
        filename = await asyncio.to_thread(download_video, text)
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'rb') as f:
                    await update.message.reply_video(
                        video=f,
                        reply_to_message_id=update.message.message_id
                    )
            except Exception as e:
                logger.warning(f"reply_video не удался, пробую document: {e}")
                with open(filename, 'rb') as f:
                    await update.message.reply_document(
                        document=f,
                        reply_to_message_id=update.message.message_id
                    )
    except Exception as e:
        logger.error(f"Ошибка при скачивании или отправке [{text}]: {e}")
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)
            logger.info(f"Файл удалён: {filename}")
        try:
            await msg.delete()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение-статус: {e}")

def main():
    # Исправление #8: чистим папку downloads от файлов прошлого запуска
    shutil.rmtree("downloads", ignore_errors=True)
    logger.info("Папка downloads очищена")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, handle_message)
    )
    print("✅ Бот запущен. Нажми Ctrl+C чтобы остановить.")
    logger.info("Бот запущен")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()