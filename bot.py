from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# ==========================
# CONFIGURATION
# ==========================
ADMIN_ID = 5692210187     # Your Admin ID
BOT_TOKEN = "8362909176:AAGqjkO7ntdCKjis6-YI5G1miHqS4Sbt2u4"   # Replace with your bot token

# Storage for lists
listA = []
listB = []

# Tracks what list admin is uploading
current_mode = {}


# ==========================
# MAIN MENU (BUTTONS)
# ==========================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📥 Upload List A", callback_data="setA")],
        [InlineKeyboardButton("📥 Upload List B", callback_data="setB")],
        [InlineKeyboardButton("🔎 Check Duplicate (Username Only)", callback_data="check")],
        [InlineKeyboardButton("♻️ Reset All", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ==========================
# /start COMMAND
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "🔍 *Duplicate Checker Bot*\n\n"
        "This bot compares List A and List B using *USERNAME ONLY*.\n"
        "If any username is missing, the bot will alert you.\n\n"
        "Please choose an option below:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


# ==========================
# BUTTON HANDLER
# ==========================
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    query = update.callback_query
    await query.answer()
    mode = query.data

    if mode == "setA":
        current_mode[query.from_user.id] = "A"
        await query.edit_message_text("📥 Please send *List A* now:", parse_mode="Markdown")

    elif mode == "setB":
        current_mode[query.from_user.id] = "B"
        await query.edit_message_text("📥 Please send *List B* now:", parse_mode="Markdown")

    elif mode == "reset":
        listA.clear()
        listB.clear()
        await query.edit_message_text("♻️ All lists have been cleared.", reply_markup=main_menu())

    elif mode == "check":
        await run_check(update, context, query)


# ==========================
# SAVING LIST DATA
# ==========================
async def save_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text
    uid = update.effective_user.id

    if uid not in current_mode:
        return

    mode = current_mode[uid]

    if mode == "A":
        global listA
        listA = text.split("\n")
        await update.message.reply_text("✅ List A saved!", reply_markup=main_menu())

    elif mode == "B":
        global listB
        listB = text.split("\n")
        await update.message.reply_text("✅ List B saved!", reply_markup=main_menu())

    current_mode.pop(uid)


# ==========================
# EXTRACT USERNAME
# ==========================
def extract_username(line):
    try:
        line = line.replace("#", "").strip()

        if "|" in line:
            username = line.split("|")[0].strip()
        else:
            username = line.strip()

        return username if username.startswith("@") else None

    except:
        return None


# ==========================
# CHECK DUPLICATES
# ==========================
async def run_check(update, context, query):

    A = [extract_username(x) for x in listA]
    B = [extract_username(x) for x in listB]

    # Detect missing usernames
    missing = []
    for i, x in enumerate(listA):
        if A[i] is None:
            missing.append(f"List A: `{x}`")

    for i, x in enumerate(listB):
        if B[i] is None:
            missing.append(f"List B: `{x}`")

    if missing:
        msg = "⚠️ *Missing Username Detected!*\n\n"
        msg += "\n".join(missing)
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=main_menu())
        return

    duplicates = []

    # A ↔ B Matches
    for ua in A:
        if ua in B:
            duplicates.append(f"{ua} — A & B")

    if not duplicates:
        await query.edit_message_text("❌ No duplicate usernames found!", reply_markup=main_menu())
        return

    output = "🎉 *Duplicate Usernames Found*\n\n"
    for dupe in duplicates:
        output += f"• `{dupe}`\n"

    await query.edit_message_text(output, parse_mode="Markdown", reply_markup=main_menu())


# ==========================
# RUN BOT
# ==========================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_list))

    print("BOT RUNNING...")
    await app.run_polling()


import asyncio
asyncio.run(main())
