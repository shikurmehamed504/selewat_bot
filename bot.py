import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"
FILE = "total.txt"

def load_total():
    if os.path.exists(FILE):
        try:
            with open(FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def save_total(total):
    with open(FILE, "w") as f:
        f.write(str(total))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    name = user.full_name
    await update.message.reply_text(
        f"السلام عليكم ورحمة الله وبركاته {name}!\n\n"
        "🕌 *Selewat Bot is now ACTIVE!*\n\n"
        "Send any number in the group to count Salawat\n"
        f"Current total: *{load_total():,}*\n\n"
        "Let’s reach 1 billion together InshaAllah!",
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
        full_name = user.full_name
        username = user.username
        display_name = f"@{username}" if username else full_name

        current_total = load_total()
        new_total = current_total + num
        save_total(new_total)

        reply = (
            f"{display_name} added {num:,} to Group Salawat\n"
            f"Total count: {new_total:,}"
        )
        
        await update.message.reply_text(reply)

    except ValueError:
        pass

if __name__ == "__main__":
    print("Selewat Bot Starting... Total starts at 0")
    
    app = ApplicationBuilder().token(TOKEN).concurrent_updates=True).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # THIS LINE FIXES THE ERROR 100%
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
