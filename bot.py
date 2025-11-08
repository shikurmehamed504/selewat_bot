import os
import threading
import asyncio
import urllib.request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

# ==================== CONFIG ====================
TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"
FILE = "/data/total.txt"
WEB_URL = "https://selewat-bot.onrender.com/total"

# ==================== FILE HANDLING ====================
def load_total():
    try:
        with open(FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_total(total):
    try:
        with open(FILE, "w") as f:
            f.write(str(total))
        print(f"SAVED TOTAL: {total}")
    except Exception as e:
        print(f"SAVE FAILED: {e}")

# ==================== TELEGRAM BOT ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"/start from {update.message.from_user.full_name}")
    await update.message.reply_text(
        "السلام عليكم ورحمة الله وبركاته\n\n"
        "SIRULWUJUD SELEWAT BOT\n\n"
        f"Current total: *{load_total():,}*\n\n"
        "Send any number = counted!\n"
        "Let’s hit 1 billion tonight InshaAllah!",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        print("NO TEXT MESSAGE")
        return
    
    text = update.message.text.strip()
    user = update.message.from_user
    name = f"@{user.username}" if user.username else user.full_name
    
    print(f"MESSAGE FROM {name}: '{text}'")

    # Ignore commands
    if text.startswith('/'):
        print("IGNORED COMMAND")
        return
    
    try:
        num = int(text)
        if num <= 0:
            print("NUMBER <= 0")
            return
            
        old = load_total()
        new = old + num
        save_total(new)
        
        await update.message.reply_text(
            f"{name} added *{num:,}* Salawat\n"
            f"Total: *{new:,}*",
            parse_mode='Markdown'
        )
        print(f"COUNTED: +{num:,} → TOTAL: {new:,}")
        
    except ValueError:
        print(f"NOT A NUMBER: {text}")

# ==================== WEB DASHBOARD ====================
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/total')
def total():
    total_count = load_total()
    return f'''
    <meta http-equiv="refresh" content="10">
    <h1 style="text-align:center; color:#2E8B57;">Selewat Total</h1>
    <h2 style="text-align:center; color:#1E90FF;">{total_count:,}</h2>
    <p style="text-align:center;">
        <a href="https://t.me/+YOUR_GROUP_LINK">Join Group</a> |
        <a href="https://t.me/sirulwujudselewatbot">@sirulwujudselewatbot</a>
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
            print("PING: Keep-alive sent")
        except:
            print("PING FAILED")

def start_keep_alive():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(keep_alive())

# ==================== MAIN ====================
if __name__ == "__main__":
    print("SELEWAT BOT STARTING... 100% ETERNAL")
    
    app = Application.builder().token(TOKEN).build()
    
    # CRITICAL: Listen to ALL messages
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))  # LISTEN TO EVERYTHING
    
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=start_keep_alive, daemon=True).start()
    
    print("LIVE 24/7 – DEBUG MODE ON – COUNTS EVERYWHERE!")
    app.run_polling(drop_pending_updates=True)
