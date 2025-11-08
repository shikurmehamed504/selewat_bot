import os
import threading
import asyncio
import urllib.request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

# ==================== CONFIG ====================
TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"
FILE = "/data/total.txt"  # RENDER PERSISTENT DISK
WEB_URL = "https://selewat-bot.onrender.com/total"  # YOUR LIVE COUNTER URL

# ENSURE /data DIRECTORY EXISTS
os.makedirs("/data", exist_ok=True)

# ==================== FILE HANDLING ====================
def load_total():
    try:
        with open(FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_total(total):
    with open(FILE, "w") as f:
        f.write(str(total))

# ==================== TELEGRAM BOT ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "السلام عليكم ورحمة الله وبركاته\n\n"
        "SIRULWUJUD SELEWAT BOT\n\n"
        f"Current total: *{load_total():,}*\n\n"
        "Send your daily selewat number\n"
        "Let’s hit 1 billion tonight InshaAllah!",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    try:
        num = int(text)
        if num <= 0:
            return
        user = update.message.from_user
        name = f"@{user.username}" if user.username else user.full_name
        old = load_total()
        new = old + num
        save_total(new)
        await update.message.reply_text(
            f"{name} added *{num:,}* Salawat\n"
            f"Total: *{new:,}*",
            parse_mode='Markdown'
        )
    except ValueError:
        pass  # Ignore non-numbers

# ==================== WEB DASHBOARD ====================
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/total')
def total():
    return f'''
    <meta http-equiv="refresh" content="10">
    <h1 style="text-align:center; font-family:Arial; color:#2E8B57;">
        Selewat Total
    </h1>
    <h2 style="text-align:center; font-family:Arial; color:#1E90FF;">
        {load_total():,}
    </h2>
    <p style="text-align:center;">
        <a href="https://t.me/+YOUR_GROUP_LINK" style="color:#25D366;">Join Group</a> |
        <a href="https://t.me/selewat_bot" style="color:#0088cc;">@selewat_bot</a>
    </p>
    '''

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, use_reloader=False)

# ==================== KEEP-ALIVE PING ====================
async def keep_alive():
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        try:
            urllib.request.urlopen(WEB_URL, timeout=10)
            print(f"Keep-alive ping sent to {WEB_URL}")
        except Exception as e:
            print(f"Ping failed: {e}")

def start_keep_alive():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(keep_alive())

# ==================== MAIN ====================
if __name__ == "__main__":
    print("Selewat Bot Starting... Total starts at 0")
    
    # Build Telegram App
    app = Application.builder().token(TOKEN).build()
    
    # Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start Flask Web Dashboard
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start Keep-Alive Ping
    threading.Thread(target=start_keep_alive, daemon=True).start()
    
    print("Bot + Web Dashboard + Keep-Alive = LIVE 24/7 – GREEN ETERNAL")
    
    # Run Bot
    app.run_polling(drop_pending_updates=True)
