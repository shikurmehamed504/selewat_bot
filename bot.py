import os
import threading
import asyncio
import urllib.request
import logging
import re  # ← ADDED: Extract numbers from Arabic/English text
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

# ==================== CONFIG ====================
TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"
DATA_DIR = "./data"
FILE = os.path.join(DATA_DIR, "total.txt")
WEB_URL = "https://selewat-bot.onrender.com/total"

# LOGGING
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== GLOBAL FILE HANDLING ====================
def ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            f.write("0")
        logger.info(f"CREATED: {FILE}")
    else:
        logger.info(f"LOADED: {FILE}")

def load_total():
    try:
        with open(FILE, "r") as f:
            return int(f.read().strip())
    except:
        save_total(0)
        return 0

def save_total(total):
    try:
        with open(FILE, "w") as f:
            f.write(str(total))
        logger.info(f"SAVED: {total}")
    except Exception as e:
        logger.error(f"SAVE FAILED: {e}")

# ==================== BOT HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = load_total()
    await update.message.reply_text(
        "السلام عليكم ورحمة الله\n\n"
        "SIRULWUJUD SELEWAT BOT\n\n"
        f"**GLOBAL TOTAL**: *{total:,}*\n\n"
        "Send any number = added to **GROUP SALAWAT**!\n"
        "Let’s hit 1 billion InshaAllah!",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    if text.startswith('/'):
        return

    # EXTRACT FIRST NUMBER FROM ANY TEXT (Arabic, English, Emojis)
    match = re.search(r'\d+', text)
    if not match:
        return
    
    num = int(match.group())
    if num <= 0:
        return

    user = update.message.from_user
    full_name = user.full_name
    old = load_total()
    new = old + num
    save_total(new)

    # REPLY IN GROUP (NOT PRIVATE)
    await update.message.reply_text(
        f"<b>{full_name}</b> added <b>{num:,}</b> to <b>Group Salawat</b>\

        f"Total count: <b>{new:,}</b>",
        parse_mode='HTML',
        reply_to_message_id=update.message.message_id  # ← SHOWS IN GROUP
    )
    logger.info(f"{full_name} +{num} → GLOBAL: {new}")

# ==================== WEB DASHBOARD ====================
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/total')
def total():
    count = load_total()
    return f'''
    <meta http-equiv="refresh" content="10">
    <h1 style="text-align:center; color:#2E8B57; font-family:Arial;">GLOBAL SALAWAT TOTAL</h1>
    <h2 style="text-align:center; color:#1E90FF; font-size:48px;">{count:,}</h2>
    <p style="text-align:center; font-size:20px; color:#333; line-height:1.8; margin:20px;">
        Join the group and send your Salawat count to contribute! <br>
        Every number you send adds to this total – help reach <b>1 BILLION</b> InshaAllah!
    </p>
    <p style="text-align:center;">
        <a href="https://t.me/sirrul_wejud"
           style="background:#25D366; color:white; padding:14px 30px; border-radius:30px;
                  text-decoration:none; font-weight:bold; font-size:18px; display:inline-block;">
            Join @sirrul_wejud Now
        </a>
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
    ensure_file()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(keep_alive()), daemon=True).start()
    
    logger.info("LIVE 24/7 – COUNTS FROM ARABIC TEXT – DASHBOARD MOTIVATES @sirrul_wejud!")
    app.run_polling(drop_pending_updates=True)
