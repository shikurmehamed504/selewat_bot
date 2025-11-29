import os
import threading
import asyncio
import urllib.request
import logging
import re
import json
from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ChatMemberHandler,
    filters, ContextTypes
)
from flask import Flask

# ==================== CONFIG ====================
TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"
DATA_DIR = "./data"
TOTAL_FILE = os.path.join(DATA_DIR, "total.txt")
CHALLENGE_FILE = os.path.join(DATA_DIR, "challenge.txt")
DAILY_FILE = os.path.join(DATA_DIR, "daily.json")
GROUPS_FILE = os.path.join(DATA_DIR, "groups.json")
USERNAMES_FILE = os.path.join(DATA_DIR, "usernames.json")
WEB_URL = "https://selewat-bot-je4s.onrender.com/total"
CHALLENGE_GOAL = 20_000_000
ALLOWED_USERS = {"Sirriwesururi", "S1emu", "Abdu_504", "QALB_33", "Reyhan728"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== FILE HANDLING ====================
def ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    for f in [TOTAL_FILE, CHALLENGE_FILE]:
        if not os.path.exists(f): open(f, "w").write("0")
    for f in [DAILY_FILE, GROUPS_FILE, USERNAMES_FILE]:
        if not os.path.exists(f): json.dump({} if f != GROUPS_FILE else [], open(f, "w"))

def load_total():
    try: return int(open(TOTAL_FILE).read().strip() or "0")
    except: return 0
def save_total(t): open(TOTAL_FILE, "w").write(str(t))

def load_challenge():
    try: return int(open(CHALLENGE_FILE).read().strip() or "0")
    except: return 0
def save_challenge(c): open(CHALLENGE_FILE, "w").write(str(c))

def load_daily():
    try: return json.load(open(DAILY_FILE)) if os.path.getsize(DAILY_FILE) > 0 else {}
    except: return {}
def save_daily(d):
    with open(DAILY_FILE, "w") as f: json.dump(d, f, ensure_ascii=False, indent=2)

def load_groups():
    try: return json.load(open(GROUPS_FILE))
    except: return []
def save_groups(g):
    with open(GROUPS_FILE, "w") as f: json.dump(g, f)

def load_usernames():
    try: return json.load(open(USERNAMES_FILE))
    except: return {}
def save_username(user_id, full_name):
    data = load_usernames()
    data[str(user_id)] = full_name
    with open(USERNAMES_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False)

# ==================== AUTO TRACK GROUPS (v21.5 CORRECT) ====================
async def track_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.my_chat_member: return
    chat = update.my_chat_member.chat
    status = update.my_chat_member.new_chat_member.status
    groups = load_groups()

    if chat.type in ["group", "supergroup"]:
        if status in ["member", "administrator"] and chat.id not in groups:
            groups.append(chat.id)
            save_groups(groups)
            logger.info(f"Bot added to group: {chat.title}")
        elif status in ["left", "kicked"] and chat.id in groups:
            groups.remove(chat.id)
            save_groups(groups)

# ==================== DAILY REPORT ====================
async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    data = load_daily()
    if yesterday not in data or not data[yesterday]:
        return

    daily_data = data[yesterday]
    total_salawat = sum(daily_data.values())
    if total_salawat == 0: return

    top_user_id = max(daily_data, key=daily_data.get)
    top_count = daily_data[top_user_id]
    usernames = load_usernames()
    top_name = usernames.get(top_user_id, "Ahbab")

    report = (
        f"<b>DAILY SALAWAT REPORT – {yesterday}</b>\n\n"
        f"Top Scorer: <b>{top_name}</b> → <b>{top_count:,}</b> Salawat\n"
        f"Total Ahbab Yesterday: <b>{len(daily_data)}</b>\n"
        f"Total Salawat Yesterday: <b>{total_salawat:,}</b>\n\n"
        f"Alhamdulillah! May Allah accept from all of us\n"
        f"Keep going → 20 Million InshaAllah!"
    )

    groups = load_groups()
    sent = 0
    for chat_id in groups[:]:
        try:
            await context.bot.send_message(chat_id=chat_id, text=report, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"Can't send to {chat_id}: {e}")
            if "blocked" in str(e).lower() or "kicked" in str(e).lower():
                groups.remove(chat_id)
                save_groups(groups)

    logger.info(f"Report sent to {sent} groups")
    data.pop(yesterday, None)
    save_daily(data)

# ==================== HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username not in ALLOWED_USERS:
        return
    total = load_total()
    chal = load_challenge()
    remaining = max(0, CHALLENGE_GOAL - chal)
    today = datetime.now().strftime("%Y-%m-%d")
    ahbab_today = len(load_daily().get(today, {}))

    await update.message.reply_text(
        f"السلام عليكم ورحمة الله وبركاته\n\n"
        f"<b>ሶስተኛው ቻሌንጅ እስካሁን የተባለው ሰለዋት</b>: <code>{total:,}</code>\n"
        f"<b>ጠቅላላ</b>: <code>{min(chal, CHALLENGE_GOAL):,} / 20,000,000</code>\n"
        f"<b>የቀረው</b>: <code>{remaining:,}</code>\n"
        f"<b>ዛሬ ሪፖርት ያደረጉ አህባቦች ብዛት</b>: <code>{ahbab_today}</code>\n\n"
        f"በእዚህ የጀምዓ የሰለዎት ዘመቻ ላይ በቻልነው ያህል በመሳተፍ የበረካው ተካፋይ እንሁን!!\n\n",
        parse_mode="HTML"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private" or update.message.from_user.is_bot:
        return

    text = update.message.text.strip()
    if text.startswith('/') or re.search(r'\*\d+\*', text):
        return

    numbers = re.findall(r'\d+', text.replace(',', '').replace('،', ''))
    if not numbers: return

    try: num = max(int(n) for n in numbers)
    except: return
    if num <= 0: return

    user_id = str(update.message.from_user.id)
    full_name = update.message.from_user.full_name or "Ahbab"
    save_username(user_id, full_name)

    total = load_total() + num
    chal = min(load_challenge() + num, CHALLENGE_GOAL)
    save_total(total)
    save_challenge(chal)

    today = datetime.now().strftime("%Y-%m-%d")
    daily = load_daily()
    daily.setdefault(today, {})
    daily[today][user_id] = daily[today].get(user_id, 0) + num
    save_daily(daily)
    ahbab_today = len(daily[today])

    await update.message.reply_text(
        f"<b>{full_name}</b> added <b>{num:,}</b>Selewat to Sirul Wejud Selewat Group\n\n"
        f"ዛሬ ሪፖርት ያደረጉ አህባቦች ብዛት: <b>{ahbab_today}</b>\n"
        f"ጠቅላላ/Total count: <b>{total:,}</b>\n"
        f"የቀረው/Remaining: <b>{CHALLENGE_GOAL - chal:,}</b>\n\n"
        f"በእዚህ የጀምዓ የሰለዎት ዘመቻ ላይ በቻልነው ያህል በመሳተፍ የበረካው ተካፋይ እንሁን!!\n"
        f"20 million እስክንደርስ ድረስ InshaAllah!\n",
        parse_mode="HTML",
        reply_to_message_id=update.message.message_id
    )

# ==================== DASHBOARD ====================
flask_app = Flask(__name__)
@flask_app.route('/')
@flask_app.route('/total')
def dashboard():
    t = load_total()
    c = min(load_challenge(), CHALLENGE_GOAL)
    r = max(0, CHALLENGE_GOAL - c)
    return f'''
    <meta http-equiv="refresh" content="15">
    <body style="margin:0;height:100vh;background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);color:white;font-family:system-ui;display:flex;flex-direction:column;justify-content:center;align-items:center;">
      <h1 style="font-size:3.5em;margin:0;">GLOBAL SALAWAT TOTAL</h1>
      <h2 style="font-size:7em;margin:20px;">{t:,}</h2>
      <p style="font-size:2em;">Challenge: <b>{c:,}/20,000,000</b><br>Remaining: <b>{r:,}</b></p>
      <a href="https://t.me/sirrul_wejud" style="margin-top:40px;background:#25D366;color:white;padding:20px 60px;border-radius:50px;text-decoration:none;font-size:2em;">Join @sirrul_wejud</a>
    </body>'''

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

# ==================== KEEP-ALIVE ====================
async def keep_alive():
    while True:
        await asyncio.sleep(180)  # Every 3 minutes
        try:
            # Correct URLs — no double /total
            urllib.request.urlopen(WEB_URL, timeout=10)           # https://.../total
            urllib.request.urlopen("https://selewat-bot-je4s.onrender.com/", timeout=10)
            logger.info("Keep-alive ping sent – bot stays awake!")
        except Exception as e:
            logger.warning(f"Keep-alive failed (normal): {e}")

# ==================== MAIN ====================
async def main():
    ensure_file()
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(keep_alive()), daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # CORRECT v21.5 WAY — NO ERROR
    app.add_handler(ChatMemberHandler(track_groups, chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER))

    app.job_queue.run_daily(daily_report, time(hour=15, minute=0))  # 6 PM EAT

    while True:
        try:
            await app.initialize()
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            logger.info("SELEWAT BOT IS LIVE – FINAL 100% WORKING!")
            while True: await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Crash: {e}")
            await asyncio.sleep(10)
        finally:
            try:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
            except: pass

if __name__ == "__main__":
    asyncio.run(main())
