import os
import threading
import asyncio
import urllib.request
import logging
import re
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

# ==================== CONFIG ====================
TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"
DATA_DIR = "./data"
TOTAL_FILE = os.path.join(DATA_DIR, "total.txt")
CHALLENGE_FILE = os.path.join(DATA_DIR, "challenge.txt")
DAILY_FILE = os.path.join(DATA_DIR, "daily.json")
WEB_URL = "https://selewat-bot.onrender.com/total"
CHALLENGE_GOAL = 20_000_000

# ONLY THESE 3 USERS CAN USE /start
ALLOWED_USERS = {"Sirriwesururi", "S1emu", "Abdu_504"}

# LOGGING
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== FILE HANDLING ====================
def ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    for file_path in [TOTAL_FILE, CHALLENGE_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("0")
            logger.info(f"CREATED: {file_path}")
    if not os.path.exists(DAILY_FILE):
        save_daily({})

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

def load_daily():
    try:
        with open(DAILY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_daily(data):
    with open(DAILY_FILE, "w") as f:
        json.dump(data, f)

# ==================== DAILY REPORT (6PM EAT) ====================
async def daily_report(context):
    today = datetime.now().strftime("%Y-%m-%d")
    data = load_daily()
    if today not in data or not data[today]:
        return

    daily_data = data[today]
    total_today = sum(daily_data.values())
    top_user = max(daily_data, key=daily_data.get)
    top_count = daily_data[top_user]

    report = (
        f"**DAILY SALAWAT REPORT – {today}**\n\n"
        f"Top Scorer Today: <b>{top_user}</b> with <b>{top_count:,}</b> Salawat!\n"
        f"Total Submissions Today: <b>{len(daily_data)}</b> Ahbab\n"
        f"Total Salawat Today: <b>{total_today:,}</b>\n\n"
        f"Alhamdulillah! Keep going until 20 Million InshaAllah!\n"
        f"ﷺ"
    )

    # SEND TO ALL GROUPS WHERE BOT IS ADMIN
    try:
        updates = await context.bot.get_updates(limit=100, allowed_updates=["my_chat_member"])
        for update in updates:
            if update.my_chat_member:
                chat = update.my_chat_member.chat
                if chat.type in ["group", "supergroup"]:
                    status = update.my_chat_member.new_chat_member.status
                    if status in ["administrator", "creator"]:
                        try:
                            await context.bot.send_message(chat_id=chat.id, text=report, parse_mode='HTML')
                        except:
                            pass
    except:
        pass

    # Reset daily
    data[today] = {}
    save_daily(data)

# ==================== BOT HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or "Unknown"

    if username not in ALLOWED_USERS:
        await update.message.reply_text(
            "السلام عليكم\n\n"
            "This command is restricted to authorized users only.\n\n"
            "Join the group to participate:\n"
            "https://t.me/sirrul_wejud",
            disable_web_page_preview=True
        )
        return

    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text(
            "السلام عليكم ورحمة الله\n\n"
            "This bot only works in the group!\n\n"
            "Join the official group:\n"
            "https://t.me/sirrul_wejud",
            disable_web_page_preview=True
        )
        return

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
    remaining = max(0, CHALLENGE_GOAL - chal)
    participants_today = len(load_daily().get(datetime.now().strftime("%Y-%m-%d"), {}))

    await update.message.reply_text(
        "السلام عليكم ورحمة الله وبركاته\n\n"
        "ሲሩል ውጁድ የሰለዋት መርከብ\n\n"
        f"**ሶስተኛው ቻሌንጅ እስካሁን የተባለው ሰለዋት**: *{total:,}*\n"
        f"**ጠቅላላ**: *{min(chal, CHALLENGE_GOAL):,} / {CHALLENGE_GOAL:,}*\n"
        f"**የቀረው**: *{remaining:,}*\n"
        f"**ዛሬ ሪፖርት ያደረጉ አህባቦች ብዛት**: *{participants_today}*\n\n"
        "በእዚህ የጀምዓ የሰለዎት ዘመቻ ላይ በቻልነው ያህል በመሳተፍ የበረካው ተካፋይ እንሁን!!\n"
        "20 million እስክንደርስ ድረስ InshaAllah\n\n",
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        return

    try:
        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            return
    except:
        return

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if text.startswith('/'):
        return

    if re.search(r'\*\d+\*', text):
        return

    clean_text = text.replace(',', '').replace('،', '')
    numbers = re.findall(r'\d+', clean_text)
    if not numbers:
        return

    num = max(int(n) for n in numbers)
    if num <= 0:
        return

    user = update.message.from_user
    full_name = user.full_name
    username = user.username or full_name

    chal = load_challenge()
    new_chal = min(chal + num, CHALLENGE_GOAL)
    total = load_total()
    new_total = total + num

    save_challenge(new_chal)
    save_total(new_total)

    today = datetime.now().strftime("%Y-%m-%d")
    daily = load_daily()
    if today not in daily:
        daily[today] = {}
    daily[today][username] = daily[today].get(username, 0) + num
    save_daily(daily)

    participants_today = len(daily.get(today, {}))
    remaining = CHALLENGE_GOAL - new_chal

    await update.message.reply_text(
        f"<b>{full_name}</b> added <b>{num:,}</b> to <b>Group Salawat</b>\n"
        f"The number of Ahbabs that submitted today: <b>{participants_today}</b>\n"
        f"Total count: <b>{new_total:,}</b>\n"
        f"Remaining Selewat from this challenge: <b>{remaining:,}</b>",
        parse_mode='HTML',
        reply_to_message_id=update.message.message_id
    )

# ==================== WEB DASHBOARD ====================
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/total')
def total():
    total_count = load_total()
    chal = min(load_challenge(), CHALLENGE_GOAL)
    remaining = max(0, CHALLENGE_GOAL - chal)
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
    
    # DAILY REPORT AT 6:00 PM EAT
    app.job_queue.run_daily(daily_report, time=datetime.time(hour=15, minute=0))
    
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(keep_alive()), daemon=True).start()
    
    logger.info("LIVE 24/7 – ALL FEATURES ACTIVE – ETERNAL SADAQAH!")
    app.run_polling(drop_pending_updates=True)
