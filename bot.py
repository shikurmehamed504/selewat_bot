import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading

TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"
FILE = "total.txt"

def load_total():
    try:
        with open(FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_total(total):
    with open(FILE, "w") as f:
        f.write(str(total))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "السلام عليكم ورحمة الله وبركاته\n\n"
        "🕌 *Selewat Bot 24/7 ETERNAL!*\n\n"
        f"Current total: *{load_total():,}*\n\n"
        "Send any number = Salawat counted!\n"
        "Let’s reach 1 billion tonight InshaAllah!",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    try:
        num = int(text)
        if num <= 0: return
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
    except:
        pass

# WEB DASHBOARD
flask_app = Flask(__name__)
@flask_app.route('/total')
def total():
    return f'<h1><center>Selewat Total</center></h1><h2><center>{load_total():,}</center></h2><meta http-equiv="refresh" content="10">'

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

if __name__ == "__main__":
    print("Selewat Bot Starting... Total starts at 0")
    app = Application(token=TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("Bot + Web Dashboard LIVE 24/7 – GREEN IN 30 SECONDS")
    app.run_polling()
