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
from flask import Flask

# ==================== CONFIG ====================
TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"
DATA_DIR = "./data"
TOTAL_FILE = os.path.join(DATA_DIR, "total.txt")
CHALLENGE_FILE = os.path.join(DATA_DIR, "challenge.txt")
DAILY_FILE = os.path.join(DATA_DIR, "daily.json")
WEB_URL = "https://selewat-bot-je4s.onrender.com/total"  # Change only if your URL changes
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
        json.dump(d, f)

# ==================== CLEAN OLD SESSIONS (ONCE AT STARTUP) ====================
async def kill_old_sessions():
    bot = Bot(token=TOKEN)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Old webhook cleared")
    except Exception as e:
        logger.warning(f"Webhook cleanup failed (normal on first start): {e}")
    finally:
        await bot.session.close()

# Run once at startup
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
        f"Top Scorer Today: <b>{top_user}</b> → <b>{top_count:,}</b> Salawat!\n"
        f"Total Submissions: <b>{len(daily_data)}</b> Ahbab\n"
        f"Total Salawat Today: <b>{total_today:,}</b>\n\n"
        f"Alhamdulillah! Keep going until 20 Million InshaAllah!\n"
        f"Allah"
    )

    # Send report to all groups where bot is admin
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
        logger.error(f"Failed to send daily report: {e}")

    # Reset today's data
    data[today] = {}
    save_daily(data)

# ==================== BOT HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or "Unknown"

    if username not in ALLOWED_USERS and update.effective_chat.type == "private":
        await update.message.reply_text("This command is restricted to authorized users.")
        return

    total = load_total()
    chal = load_challenge()
    remaining = max(0, CHALLENGE_GOAL - chal)
    today_str = datetime.now().strftime("%Y-%m-%d")
    participants_today = len(load_daily().get(today_str, {}))

    await update.message.reply_text(
        f"السلام عليكم ورحمة الله وبركاته\n\n"
        f"<b>GLOBAL TOTAL</b>: <code>{total:,}</code>\n"
        f"<b>CURRENT CHALLENGE</b>: <code>{min(chal, CHALLENGE_GOAL):,} / {CHALLENGE_GOAL:,}</code>\n"
        f"<b>Remaining</b>: <code>{remaining:,}</code>\n"
        f"<b>Ahbab Today</b>: <code>{participants_today}</code>\n\n"
        f"Send any number → added to group total!\n\n"
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

    username = update.message.from_user.username or update.message.from_user.full_name
    full_name = update.message.from_user.full_name

    # Update totals
    total = load_total() + num
    chal = min(load_challenge() + num, CHALLENGE_GOAL)
    save_total(total)
    save_challenge(chal)

    # Update daily
    today = datetime.now().strftime("%Y-%m-%d")
    daily = load_daily()
    daily.setdefault(today, {})
    daily[today][username] = daily[today].get(username, 0) + num
    save_daily(daily)

    # Reply
    await update.message.reply_text(
        f"<b>{full_name}</b> sent <b>{num:,}</b> Salawat\n\n"
        f"Global Total: <b>{total:,}</b>\n"
        f"Remaining to 20M: <b>{CHALLENGE_GOAL - chal:,}</b>",
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
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Salawat Counter</title>
        <meta http-equiv="refresh" content="15">
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100vh; margin: 0; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; }}
            h1 {{ font-size: 3em; margin-bottom: 10px; text-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
            h2 {{ font-size: 6em; margin: 20px 0; font-weight: bold; text-shadow: 0 6px 20px rgba(0,0,0,0.4); }}
            .btn {{ background: #25D366; padding: 18px 50px; font-size: 24px; border-radius: 50px; text-decoration: none; color: white; margin-top: 30px; box-shadow: 0 8px 20px rgba(0,0,0,0.3); }}
            .btn:hover {{ background: #1eba57; transform: scale(1.05); transition: 0.3s; }}
        </style>
    </head>
    <h1>GLOBAL SALAWAT TOTAL</h1>
    <h2>{t:,}</h2>
    <p style="font-size:24px;">
        Current Challenge: <b>{c:,} / {CHALLENGE_GOAL:,}</b><br>
        Remaining: <b>{r:,}</b>
    </p>
    <a href="https://t.me/sirrul_wejud" class="btn">Join @sirrul_wejud Now</a>
    </html>
    '''

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, use_reloader=False)

async def keep_alive():
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        try:
            urllib.request.urlopen(WEB_URL, timeout=10)
            logger.info("Keep-alive ping sent")
        except Exception as e:
            logger.warning(f"Keep-alive failed: {e}")

# ==================== MAIN – BULLETPROOF FOREVER ====================
async def main():
    # Start Flask web server in background
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("Flask dashboard started")

    # Start keep-alive pinger
    threading.Thread(target=lambda: asyncio.run(keep_alive()), daemon=True).start()

    # Build bot application
    app = Application.builder().token(TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.job_queue.run_daily(daily_report, time(hour=15, minute=0))  # 6 PM EAT

    # Infinite restart loop
    while True:
        try:
            logger.info("Starting Telegram bot polling...")
            await app.initialize()
            await app.start()
            await app.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
            logger.info("Bot is running – Alhamdulillah!")

            # Keep alive until error or stop
            while True:
                await asyncio.sleep(3600)

        except Exception as e:
            logger.error(f"Bot crashed ({type(e).__name__}: {e}) → restarting in 10 seconds...")
            await asyncio.sleep(10)

        finally:
            # Clean shutdown
            try:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
            except:
                pass

if __name__ == "__main__":
    logger.info("SELEWAT BOT STARTING – FINAL BULLETPROOF VERSION")
    ensure_file()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user – Allah")
    except Exception as fatal:
        logger.critical(f"Fatal error: {fatal}")
