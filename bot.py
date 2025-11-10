import os
import threading
import asyncio
import urllib.request
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

# ==================== CONFIG ====================
TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"
DATA_DIR = "./data"
TOTAL_FILE = os.path.join(DATA_DIR, "total.txt")
CHALLENGE_FILE = os.path.join(DATA_DIR, "challenge.txt")
WEB_URL = "https://selewat-bot.onrender.com/total"
CHALLENGE_GOAL = 10_000_000  # 10 million per challenge

# LOGGING
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== FILE HANDLING ====================
def ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(TOTAL_FILE):
        with open(TOTAL_FILE, "w") as f:
            f.write("0")
        logger.info(f"CREATED: {TOTAL_FILE}")
    if not os.path.exists(CHALLENGE_FILE):
        with open(CHALLENGE_FILE, "w") as f:
            f.write("0")
        logger.info(f"CREATED: {CHALLENGE_FILE}")

def load_total():
    try:
        with open(TOTAL_FILE, "r") as f:
            return int(f.read().strip())
    except:
        save_total(0)
        return 0

def save_total(total):
    with open(TOTAL_FILE, "w") as f:
        f.write(str(total))

def load_challenge():
    try:
        with open(CHALLENGE_FILE, "r") as f:
            return int(f.read().strip())
    except:
        save_challenge(0)
        return 0

def save_challenge(chal):
    with open(CHALLENGE_FILE, "w") as f:
        f.write(str(chal))

# ==================== BOT HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    # BLOCK PRIVATE CHAT
    if chat.type == "private":
        await update.message.reply_text(
            "السلام عليكم\n\n"
            "This bot only works in the group!\n\n"
            "Join the official group:\n"
            "https://t.me/sirrul_wejud",
            disable_web_page_preview=True
        )
        return

    # CHECK IF BOT IS ADMIN
    try:
        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            await update.message.reply_text(
                "Please make me an admin first to count Salawat!\n"
                "Go to Group Settings → Administrators → Add @sirulwujudselewatbot"
            )
            return
    except Exception as e:
        logger.error(f"ADMIN CHECK FAILED: {e}")
        return

    total = load_total()
    chal = load_challenge()
    remaining = CHALLENGE_GOAL - chal
    await update.message.reply_text(
        "السلام عليكم ورحمة الله\n\n"
        "SIRULWUJUD SELEWAT BOT\n\n"
        f"**GLOBAL TOTAL**: *{total:,}*\n"
        f"**CURRENT CHALLENGE**: *{chal:,} / {CHALLENGE_GOAL:,}*\n"
        f"**Remaining**: *{remaining:,}*\n\n"
        "Send any number = added to **GROUP SALAWAT**!\n"
        "Let’s hit 10 million per challenge InshaAllah!",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    # BLOCK PRIVATE CHAT
    if chat.type == "private":
        return

    # CHECK IF BOT IS ADMIN
    try:
        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            return
    except Exception as e:
        logger.error(f"ADMIN CHECK FAILED: {e}")
        return

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if text.startswith('/'):
        return

    # EXTRACT NUMBER: 1,200 or ١٨٥٠ or 1200
    num_str = re.sub(r'[^\d]', '', text)  # Remove commas, spaces, Arabic letters
    if not num_str:
        return
    try:
        num = int(num_str)
    except:
        return
    if num <= 0:
        return

    user = update.message.from_user
    full_name = user.full_name

    # Update challenge & total
    chal = load_challenge()
    new_chal = chal + num
    total = load_total()
    new_total = total + num

    # Check if goal reached
    if new_chal >= CHALLENGE_GOAL:
        excess = new_chal - CHALLENGE_GOAL
        new_chal = excess
        save_challenge(new_chal)
        save_total(new_total)
        await update.message.reply_text(
            f"<b>CHALLENGE COMPLETED!</b> {CHALLENGE_GOAL:,} Salawat achieved!\n"
            f"<b>Starting new challenge...</b>\n"
            f"<b>{full_name}</b> added <b>{num:,}</b> to <b>Group Salawat</b>\n"
            f"Total count: <b>{new_total:,}</b>\n"
            f"Remaining from new challenge: <b>{CHALLENGE_GOAL - new_chal:,}</b>",
            parse_mode='HTML',
            reply_to_message_id=update.message.message_id
        )
    else:
        save_challenge(new_chal)
        save_total(new_total)
        remaining = CHALLENGE_GOAL - new_chal
        await update.message.reply_text(
            f"<b>{full_name}</b> added <b>{num:,}</b> to <b>Group Salawat</b>\n"
            f"Total count: <b>{new_total:,}</b>\n"
            f"Remaining from this challenge: <b>{remaining:,}</b>",
            parse_mode='HTML',
            reply_to_message_id=update.message.message_id
        )
    logger.info(f"{full_name} +{num} → TOTAL: {new_total} | CHALLENGE: {new_chal}")

# ==================== WEB DASHBOARD ====================
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/total')
def total():
    total_count = load_total()
    chal = load_challenge()
    remaining = CHALLENGE_GOAL - chal
    return f'''
    <meta http-equiv="refresh" content="10">
    <h1 style="text-align:center; color:#2E8B57; font-family:Arial;">GLOBAL SALAWAT TOTAL</h1>
    <h2 style="text-align:center; color:#1E90FF; font-size:48px;">{total_count:,}</h2>
    <p style="text-align:center; font-size:20px; color:#333;">
        Current Challenge: {chal:,} / {CHALLENGE_GOAL:,}<br>
        Remaining: <b>{remaining:,}</b>
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
    
    logger.info("LIVE 24/7 – CHALLENGE SYSTEM – COMMA + ARABIC – ADMIN-ONLY!")
    app.run_polling(drop_pending_updates=True)
