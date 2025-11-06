import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# === YOUR BOT TOKEN ===
TOKEN = "8229668167:AAFmHYkIfwzTNMa_SzPETJrCJSfE42CPmNA"

# === FILE TO SAVE TOTAL (persistent on Render) ===
FILE = "total.txt"

# === LOAD TOTAL FROM FILE (or start at 0) ===
def load_total():
    if os.path.exists(FILE):
        try:
            with open(FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

# === SAVE TOTAL TO FILE ===
def save_total(total):
    with open(FILE, "w") as f:
        f.write(str(total))

# === MESSAGE HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    
    try:
        # Only accept positive numbers
        num = int(text)
        if num <= 0:
            return

        # Get user name
        user = update.message.from_user
        full_name = user.full_name
        username = user.username
        display_name = f"@{username}" if username else full_name

        # Update total
        current_total = load_total()
        new_total = current_total + num
        save_total(new_total)

        # Beautiful reply just like your original bot
        reply = (
            f"{display_name} added {num:,} to Group Salawat\n"
            f"Total count: {new_total:,}"
        )
        
        await update.message.reply_text(reply)

    except ValueError:
        # Not a number → ignore silently
        pass
    except Exception as e:
        print(f"Error: {e}")

# === START THE BOT ===
if __name__ == "__main__":
    print("Selewat Bot Starting...")
    print("Total starts at 0")
    print("Send any number in your group to count Salawat!")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handle all text messages that are not commands
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is LIVE 24/7 on Render.com")
    app.run_polling(drop_pending_updates=True)
