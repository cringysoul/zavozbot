import os
import re
import random
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

import yt_dlp

load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ID пользователя которому отвечаем гифкой
TARGET_USER_ID = 5263879474 

# file_id гифки
GIF_FILES = [
    "CgACAgIAAxkBAAFDzphpqBhs98iDDaVLT3lihB3ITR1guwACGZcAAgIQGUtNaOuySJMIDToE",
    "CgACAgIAAxkBAAFD2ippqHrFSlvHfAABVctvgHyswu5uSVEAAniVAAKe3PlIJ3fVLt_zTa86BA",
]

def is_valid_url(text):
    pattern = r'(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com|instagram\.com/reel|twitter\.com|x\.com|youtube\.com|youtu\.be)'
    return bool(re.search(pattern, text))

def download_video(url: str):
    os.makedirs("downloads", exist_ok=True)
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'merge_output_format': 'mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        filename = os.path.splitext(filename)[0] + '.mp4'
        return filename

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    # Гифка с шансом 15%
    if update.message.from_user and update.message.from_user.id == TARGET_USER_ID:
        if random.randint(1, 100) <= 15:
            await update.message.reply_animation(
                animation=random.choice(GIF_FILES),
                reply_to_message_id=update.message.message_id
            )

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
            except Exception:
                with open(filename, 'rb') as f:
                    await update.message.reply_document(
                        document=f,
                        reply_to_message_id=update.message.message_id
                    )
    except Exception:
        pass
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)
        try:
            await msg.delete()
        except Exception:
            pass

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    print("✅ Бот запущен. Нажми Ctrl+C чтобы остановить.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()