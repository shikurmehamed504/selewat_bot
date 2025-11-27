import os
import threading
import asyncio
import urllib.request
import logging
import re
import json
from datetime import datetime, time
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import Conflict
from flask import Flask

# ==================== CONFIG ====================
TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"
DATA_DIR = "./data"
TOTAL_FILE = os.path.join(DATA_DIR, "total.txt")
CHALLENGE_FILE = os.path.join(DATA_DIR, "challenge.txt")
DAILY_FILE = os.path.join(DATA_DIR, "daily.json")
WEB_URL = "https://selewat-bot-je4s.onrender.com/total"  # ← change if your URL is different
CHALLENGE_GOAL = 20_000_000
ALLOWED_USERS = {"Sirriwesururi", "S1emu", "Abdu_504"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== FORCE KILL OLD SESSIONS (MUST BE FIRST) ====================
async def kill_old_sessions():
    bot = Bot(token=TOKEN)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        updates = await bot.get_updates()
        if updates:
            await bot.get_updates(offset=updates[-1].update_id + 1)
            logger.info(f"Cleared {len(updates)} pending updates")
    except Exception as e:
        logger.warning(f"Old session cleanup failed (normal): {e}")
    finally:
        await bot.session.close()

# Run immediately when script starts
try:
    asyncio.run(kill_old_sessions())
except:
    pass

# ==================== FILE HANDLING ====================
def ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    for file_path in [TOTAL_FILE, CHALLENGE_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("0")
    if not os.path.exists(DAILY_FILE):
        with open(DAILY_FILE, "w") as f:
            json.dump({}, f)

def load_total():    return int(open(TOTAL_FILE).read().strip() or "0")
def save_total(t):   open(TOTAL_FILE, "w").write(str(t))
def load_challenge():return int(open(CHALLENGE_FILE).read().strip() or "0")
def save_challenge(c):open(CHALLENGE_FILE, "w").write(str(c))
def load_daily():    return json.load(open(DAILY_FILE)) if os.path.getsize(DAILY_FILE) > 0 else {}
def save_daily(d):   json.dump(d, open(DAILY_FILE, "w"))

# ==================== DAILY REPORT (6 PM EAT = 15:00 UTC) ====================
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
    # Send to all groups where bot is admin
    try:
        updates = await context.bot.get_updates(limit=100)
        for update in updates:
            if update.my_chat_member:
                chat = update.my_chat_member.chat
                if chat.type in ["group", "supergroup"]:
                    status = update.my_chat_member.new_chat_member.status
                    if status in ["administrator", "creator"]:
                        await context.bot.send_message(chat_id=chat.id, text=report, parse_mode='HTML')
    except: pass
    data[today] = {}
    save_daily(data)

# ==================== BOT HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or "Unknown"
    if username not in ALLOWED_USERS and update.effective_chat.type == "private":
        await update.message.reply_text("This command is restricted.")
        return
    # ... (your full /start message – same as before)
    total = load_total()
    chal = load_challenge()
    remaining = max(0, CHALLENGE_GOAL - chal)
    participants_today = len(load_daily().get(datetime.now().strftime("%Y-%m-%d"), {}))
    await update.message.reply_text(
        f"السلام عليكم ورحمة الله وبركاته\n\n"
        f"**GLOBAL TOTAL**: *{total:,}*\n"
        f"**CURRENT CHALLENGE**: *{min(chal, CHALLENGE_GOAL):,} / {CHALLENGE_GOAL:,}*\n"
        f"**Remaining**: *{remaining:,}*\n"
        f"**Ahbab Today**: *{participants_today}*\n\n"
        f"Send any number = added to group total!\n"
        f"Dashboard: {WEB_URL}",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private": return
    text = update.message.text.strip()
    if text.startswith('/') or re.search(r'\*\d+\*', text): return
    numbers = re.findall(r'\d+', text.replace(',', '').replace('،', ''))
    if not numbers: return
    num = max(int(n) for n in numbers)
    if num <= 0: return

    username = update.message.from_user.username or update.message.from_user.full_name
    total = load_total() + num
    chal = min(load_challenge() + num, CHALLENGE_GOAL)
    save_total(total)
    save_challenge(chal)

    today = datetime.now().strftime("%Y-%m-%d")
    daily = load_daily()
    daily.setdefault(today, {})[username] = daily[today].get(username, 0) + num
    save_daily(daily)

    await update.message.reply_text(
        f"<b>{update.message.from_user.full_name}</b> added <b>{num:,}</b>\n"
        f"Total: <b>{total:,}</b>\n"
        f"Remaining: <b>{CHALLENGE_GOAL - chal:,}</b>",
        parse_mode='HTML',
        reply_to_message_id=update.message.message_id
    )

# ==================== WEB DASHBOARD ====================
flask_app = Flask(__name__)
@flask_app.route('/')
@flask_app.route('/total')
def total():
    t = load_total()
    c = min(load_challenge(), CHALLENGE_GOAL)
    r = max(0, CHALLENGE_GOAL - c)
    return f'''
    <meta http-equiv="refresh" content="10">
    <h1 style="text-align:center; color:#2E8B57;">GLOBAL SALAWAT TOTAL</h1>
    <h2 style="text-align:center; color:#1E90FF; font-size:60px;">{t:,}</h2>
    <p style="text-align:center; font-size:22px;">
        Current Challenge: {c:,} / {CHALLENGE_GOAL:,}<br>
        Remaining: <b>{r:,}</b>
    </p>
    <p style="text-align:center;">
        <a href="https://t.me/sirrul_wejud" style="background:#25D366; color:white; padding:15px 40px; border-radius:50px; text-decoration:none; font-size:20px;">
            Join @sirrul_wejud Now
        </a>
    </p>
    '''

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, use_reloader=False)

async def keep_alive():
    while True:
        await asyncio.sleep(300)
        try:
            urllib.request.urlopen(WEB_URL, timeout=10)
            logger.info("Keep-alive ping sent")
        except: pass

# ==================== MAIN – BULLETPROOF LOOP ====================
if __name__ == "__main__":
    logger.info("SELEWAT BOT STARTING – FINAL BULLETPROOF VERSION")
    ensure_file()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.job_queue.run_daily(daily_report, time(hour=15, minute=0))

    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(keep_alive()), daemon=True).start()

    # INFINITE RESTART LOOP – NEVER DIES
    while True:
        try:
            logger.info("Starting polling...")
            app.run_polling(drop_pending_updates=True)
        except Conflict:
            logger.warning("Conflict detected → restarting in 15 seconds...")
            asyncio.run(asyncio.sleep(15))
        except Exception as e:
            logger.error(f"Bot crashed ({e}) → restarting in 10 seconds...")
            asyncio.run(asyncio.sleep(10))
