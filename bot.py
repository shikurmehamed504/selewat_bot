import os
import threading
import asyncio
import urllib.request
import logging
import re
import json
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

# ==================== CONFIG ====================
TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"
DATA_DIR = "./data"
TOTAL_FILE = os.path.join(DATA_DIR, "total.txt")
CHALLENGE_FILE = os.path.join(DATA_DIR, "challenge.txt")
DAILY_FILE = os.path.join(DATA_DIR, "daily.json")
WEB_URL = "https://selewat-bot-je4s.onrender.com/total"
CHALLENGE_GOAL = 20_000_000
ALLOWED_USERS = {"Sirriwesururi", "S1emu", "Abdu_504"}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

def load_total():
    try:
        return int(open(TOTAL_FILE).read().strip() or "0")
    except:
        return 0

def save_total(t):
    open(TOTAL_FILE, "w").write(str(t))

def load_challenge():
    try:
        return int(open(CHALLENGE_FILE).read().strip() or "0")
    except:
        return 0

def save_challenge(c):
    open(CHALLENGE_FILE, "w").write(str(c))

def load_daily():
    try:
        if os.path.getsize(DAILY_FILE) == 0:
            return {}
        return json.load(open(DAILY_FILE))
    except:
        return {}

def save_daily(d):
    with open(DAILY_FILE, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ==================== CLEAN OLD SESSIONS ====================
async def kill_old_sessions():
    from telegram import Bot
    bot = Bot(token=TOKEN)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Old webhook deleted")
    except Exception as e:
        logger.warning(f"Webhook cleanup failed: {e}")
    finally:
        await bot.session.close()

try:
    asyncio.run(kill_old_sessions())
except:
    pass

# ==================== DAILY REPORT – 6 PM EAT (15:00 UTC) ====================
async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%Y-%m-%d")
    data = load_daily()
    if today not in data or not data[today]:
        return

    daily_data = data[today]
    total_today = sum(daily_data.values())
    if total_today == 0:
        return

    top_user = max(daily_data, key=daily_data.get)
    top_count = daily_data[top_user]

    report = (
        f"<b>DAILY SALAWAT REPORT – {today}</b>\n\n"
        f"Top Scorer: <b>{top_user}</b> → <b>{top_count:,}</b> Salawat\n"
        f"Total Ahbab Today: <b>{len(daily_data)}</b>\n"
        f"Total Salawat Today: <b>{total_today:,}</b>\n\n"
        f"Alhamdulillah! May Allah accept from all of us\n"
        f"Keep going until 20 Million InshaAllah!"
    )

    try:
        updates = await context.bot.get_updates(limit=100)
        sent = 0
        for update in updates:
            if update.my_chat_member:
                chat = update.my_chat_member.chat
                status = update.my_chat_member.new_chat_member.status
                if chat.type in ["group", "supergroup"] and status in ["administrator", "creator"]:
                    await context.bot.send_message(chat_id=chat.id, text=report, parse_mode='HTML')
                    sent += 1
        logger.info(f"Daily report sent to {sent} groups")
    except Exception as e:
        logger.error(f"Daily report failed: {e}")

    data[today] = {}
    save_daily(data)

# ==================== BOT HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or "NoUsername"

    if username not in ALLOWED_USERS and update.effective_chat.type == "private":
        await update.message.reply_text("This bot is for group use only.")
        return

    total = load_total()
    chal = load_challenge()
    remaining = max(0, CHALLENGE_GOAL - chal)
    today_str = datetime.now().strftime("%Y-%m-%d")
    ahbab_today = len(load_daily().get(today_str, {}))

    await update.message.reply_text(
        f"السلام عليكم ورحمة الله وبركاته\n\n"
        f"<b>GLOBAL TOTAL</b>: <code>{total:,}</code>\n"
        f"<b>CURRENT CHALLENGE</b>: <code>{min(chal, CHALLENGE_GOAL):,} / 20,000,000</code>\n"
        f"<b>Remaining</b>: <code>{remaining:,}</code>\n"
        f"<b>Ahbab Today</b>: <code>{ahbab_today}</code>\n\n"
        f"Send any number → it will be added to group total!\n\n"
        f"Live Dashboard → {WEB_URL}",
        parse_mode='HTML'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    text = update.message.text.strip()
    if text.startswith('/') or re.search(r'\*\d+\*', text):
        return

    numbers = re.findall(r'\d+', text.replace(',', '').replace('،', ''))
    if not numbers:
        return

    try:
        num = max(int(n) for n in numbers)
    except:
        return
    if num <= 0:
        return

    full_name = update.message.from_user.full_name
    username = update.message.from_user.username or full_name

    # Update global totals
    total = load_total() + num
    chal = min(load_challenge() + num, CHALLENGE_GOAL)
    save_total(total)
    save_challenge(chal)

    # Update daily stats
    today = datetime.now().strftime("%Y-%m-%d")
    daily = load_daily()
    daily.setdefault(today, {})
    daily[today][username] = daily[today].get(username, 0) + num
    save_daily(daily)
    ahbab_today = len(daily[today])

    # BEAUTIFUL REPLY – EXACTLY AS YOU WANTED
    await update.message.reply_text(
        f"<b>{full_name}</b> added <b>{num:,}</b> to Sirul Wjud Salawat Group\n\n"
        f"The number of Ahbabs that submitted today: <b>{ahbab_today}</b>\n"
        f"Total count: <b>{total:,}</b>\n"
        f"Remaining Salawat from this challenge: <b>{CHALLENGE_GOAL - chal:,}</b>",
        parse_mode='HTML',
        reply_to_message_id=update.message.message_id
    )

# ==================== WEB DASHBOARD ====================
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/total')
def dashboard():
    t = load_total()
    c = min(load_challenge(), CHALLENGE_GOAL)
    r = max(0, CHALLENGE_GOAL - c)
    return f'''
    <!DOCTYPE html>
 <html>
 <head>
     <meta charset="UTF-8">
     <meta name="viewport" content="width=device-width, initial-scale=1.0">
     <title>20 Million Salawat</title>
     <meta http-equiv="refresh" content="15">
     <style>
         body {{ margin:0; height:100vh; background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); color:white; font-family: system-ui; display:flex; flex-direction:column; justify-content:center; align-items:center; }}
         h1 {{ font-size: 3.5rem; margin:0; text-shadow: 0 0 20px rgba(255,255,255,0.5); }}
         h2 {{ font-size: 7rem; margin:20px 0; font-weight:900; }}
         .info {{ font-size: 1.8rem; text-align:center; }}
         .btn {{ margin-top:40px; background:#25D366; padding:20px 60px; font-size:2rem; border-radius:50px; text-decoration:none; color:white; box-shadow:0 10px 30px rgba(0,0,0,0.5); }}
     </style>
 </head>
 <body>
     <h1>GLOBAL SALAWAT TOTAL</h1>
     <h2>{t:,}</h2>
     <div class="info">
         Current Challenge: <b>{c:,} / 20,000,000</b><br>
         Remaining: <b>{r:,}</b>
     </div>
     <a href="https://t.me/sirrul_wejud" class="btn">Join @sirrul_wejud</a>
 </body>
 </html>
    '''

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, use_reloader=False)

async def keep_alive():
    while True:
        await asyncio.sleep(300)
        try:
            urllib.request.urlopen(WEB_URL, timeout=10)
        except:
            pass

# ==================== MAIN – BULLETPROOF ====================
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("Web dashboard started")

    threading.Thread(target=lambda: asyncio.run(keep_alive()), daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.job_queue.run_daily(daily_report, time(hour=15, minute=0))

    while True:
        try:
            logger.info("Starting bot...")
            await app.initialize()
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            logger.info("Bot is LIVE – Alhamdulillah!")
            while True:
                await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Crash: {e} → restarting in 10s")
            await asyncio.sleep(10)
        finally:
            try:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
            except:
                pass

if __name__ == "__main__":
    logger.info("SELEWAT BOT STARTING – FINAL PERFECT VERSION")
    ensure_file()
    asyncio.run(main())
