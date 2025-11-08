import os
import threading
import asyncio
import urllib.request
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

# ==================== CONFIG ====================
TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"
FILE = "/data/total.txt"
WEB_URL = "https://selewat-bot.onrender.com/total"

# LOGGING
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== GLOBAL FILE HANDLING ====================
def ensure_file():
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            f.write("0")
        logger.info(f"CREATED GLOBAL FILE: {FILE} with 0")
    else:
        logger.info(f"GLOBAL FILE EXISTS: {FILE}")

def load_total():
    try:
        with open(FILE, "r") as f:
            total = int(f.read().strip())
            logger.info(f"GLOBAL TOTAL LOADED: {total}")
            return total
    except:
        logger.warning("FILE CORRUPTED → STARTING FROM 0")
        save_total(0)
        return 0

def save_total(total):
    try:
        with open(FILE, "w") as f:
            f.write(str(total))
        logger.info(f"GLOBAL TOTAL SAVED: {total}")
    except Exception as e:
        logger.error(f"SAVE FAILED: {e}")

# ==================== TELEGRAM BOT ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    logger.info(f"/start from {update.message.from_user.full_name} in {chat_type}")
    await update.message.reply_text(
        "السلام عليكم ورحمة الله\n\n"
        "SIRULWUJUD SELEWAT BOT\n\n"
        f"**GLOBAL TOTAL**: *{load_total():,}*\n\n"
        "Send any number = counted in **GLOBAL TOTAL**!\n"
        "Let’s hit 1 billion tonight InshaAllah!",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if text.startswith('/'):
        return
    try:
        num = int(text)
        if num <= 0:
            return
        user = update.message.from_user
        name = f"@{user.username}" if user.username else user.full_name
        chat_type = update.message.chat.type
        old = load_total()
        new = old + num
        save_total(new)
        await update.message.reply_text(
            f"{name} added {num:,} Salawat\n"
            f"**GLOBAL TOTAL**: {new:,}\n"
            f"({chat_type})"
        )
        logger.info(f"ADDED {num} by {name} in {chat_type} → GLOBAL: {new}")
    except ValueError:
        pass

# ==================== WEB DASHBOARD ====================
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/total')
def total():
    count = load_total()
    return f'''
    <meta http-equiv="refresh" content="10">
    <h1 style="text-align:center; color:#2E8B57; font-family:Arial;">GLOBAL SELEWAT TOTAL</h1>
    <h2 style="text-align:center; color:#1E90FF; font-size:48px;">{count:,}</h2>
    <p style="text-align:center; font-size:20px;">
        <a href="https://t.me/+YOUR_GROUP_LINK" style="color:#25D366; text-decoration:none;">Join Group</a> |
        <a href="https://t.me/sirulwujudselewatbot" style="color:#0088cc; text-decoration:none;">@sirulwujudselewatbot</a>
    </p>
    '''

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, use_reloader=False)

# ==================== KEEP-ALIVE ====================
async def keep_alive():
    while True:
        await asyncio.sleep(300)
        try:
            urllib.request.urlopen(WEB_URL, timeout=10)
            logger.info("PING: Keep-alive sent")
        except:
            pass

# ==================== MAIN ====================
if __name__ == "__main__":
    logger.info("GLOBAL SELEWAT BOT STARTING...")
    ensure_file()  # ← ONLY CREATES IF MISSING
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(keep_alive()), daemon=True).start()
    
    logger.info("LIVE 24/7 – GLOBAL TOTAL NEVER RESETS – ETERNAL!")
    app.run_polling(drop_pending_updates=True)
