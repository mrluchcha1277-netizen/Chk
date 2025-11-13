from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import random

# ==========================
# CONFIG
# ==========================
ADMIN_ID = 5692210187
BOT_TOKEN = "8362909176:AAHKdyvrEARiUh8MBsQBbORQi2SByd5Tl9Q"   # <-- Put your bot token here

listA = []
listB = []

current_mode = {}
waiting_for_pickup_number = False
BOT_ACTIVE = True    # BOT ON/OFF SYSTEM


# ==========================
# BUTTON MENU
# ==========================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📥 Upload List A", callback_data="setA")],
        [InlineKeyboardButton("📥 Upload List B", callback_data="setB")],
        [InlineKeyboardButton("🔎 Check Duplicate", callback_data="check")],
        [InlineKeyboardButton("🎯 Pickup Random Winners", callback_data="pickup")],
        [InlineKeyboardButton("♻️ Reset All", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ==========================
# /start
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "🔍 *Duplicate Cleaner Bot*\n\n"
        "✔ Username-only system\n"
        "✔ Missing usernames auto removed\n"
        "✔ Duplicate removed\n"
        "✔ Pure winner system\n"
        "✔ Bot ON/OFF control\n\n"
        "Use the buttons below:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# ==========================
# /on
# ==========================
async def turn_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE

    if update.effective_user.id != ADMIN_ID:
        return

    BOT_ACTIVE = True
    await update.message.reply_text(
        "🟢 Bot is now *ON*.\nAll systems activated!",
        parse_mode="Markdown"
    )


# ==========================
# /off
# ==========================
async def turn_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE

    if update.effective_user.id != ADMIN_ID:
        return

    BOT_ACTIVE = False
    await update.message.reply_text(
        "🔴 Bot is now *OFF*.\nAll systems deactivated!",
        parse_mode="Markdown"
    )


# ==========================
# /help
# ==========================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = (
        "📘 *Available Commands*\n\n"
        "/start - Open Bot Menu\n"
        "/on - Turn Bot ON\n"
        "/off - Turn Bot OFF\n"
        "/help - Show command list\n"
        "/pickup - Random winner picker\n\n"
        "Buttons:\n"
        "📥 Upload List A\n"
        "📥 Upload List B\n"
        "🔎 Check Duplicate\n"
        "🎯 Pickup Random Winners\n"
        "♻️ Reset All\n"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


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
# CLEAN LIST GENERATOR
# ==========================
def clean_listA():
    usernames = [extract_username(x) for x in listA]
    usernames = [u for u in usernames if u is not None]

    pure = []
    for u in usernames:
        if u not in pure:
            pure.append(u)

    return pure


# ==========================
# BUTTON HANDLER
# ==========================
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_pickup_number

    if update.effective_user.id != ADMIN_ID:
        return

    query = update.callback_query
    await query.answer()

    if not BOT_ACTIVE:
        await query.edit_message_text("⚠️ Bot is OFF. Use /on to activate.")
        return

    mode = query.data

    if mode == "setA":
        current_mode[query.from_user.id] = "A"
        await query.edit_message_text("📥 Send *List A* now:", parse_mode="Markdown")

    elif mode == "setB":
        current_mode[query.from_user.id] = "B"
        await query.edit_message_text("📥 Send *List B* now:", parse_mode="Markdown")

    elif mode == "reset":
        listA.clear()
        listB.clear()
        await query.edit_message_text("♻️ All lists cleared.", reply_markup=main_menu())

    elif mode == "check":
        await run_check(update, context, query)

    elif mode == "pickup":
        if len(listA) == 0:
            await query.edit_message_text("⚠️ List A is empty. Upload List A first.")
            return

        waiting_for_pickup_number = True
        await query.edit_message_text(
            "🎯 How many winners do you want? (1–100000)\nExample: 10"
        )


# ==========================
# SAVE LIST DATA
# ==========================
async def save_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_pickup_number

    if update.effective_user.id != ADMIN_ID:
        return

    if not BOT_ACTIVE:
        await update.message.reply_text("⚠️ Bot is OFF. Use /on to activate.")
        return

    if waiting_for_pickup_number:
        await pickup_number_handler(update, context)
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
# DUPLICATE CHECK
# ==========================
async def run_check(update, context, query):
    if not BOT_ACTIVE:
        await query.edit_message_text("⚠️ Bot is OFF. Use /on to activate.")
        return

    A = [extract_username(x) for x in listA]
    B = [extract_username(x) for x in listB]

    missing = []
    for i, row in enumerate(listA):
        if A[i] is None:
            missing.append(f"List A: `{row}`")
    for i, row in enumerate(listB):
        if B[i] is None:
            missing.append(f"List B: `{row}`")

    if missing:
        msg = "⚠️ *Missing Username Detected!*\n\n" + "\n".join(missing)
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=main_menu())
        return

    duplicates = []
    for ua in A:
        if ua in B and ua is not None:
            duplicates.append(ua)

    if not duplicates:
        await query.edit_message_text("❌ No duplicates found.", reply_markup=main_menu())
        return

    res = "🎉 *Duplicate Usernames Found*\n\n"
    for d in duplicates:
        res += f"• `{d}`\n"

    await query.edit_message_text(res, parse_mode="Markdown", reply_markup=main_menu())


# ==========================
# RANDOM PURE WINNER PICK
# ==========================
async def pickup_number_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_pickup_number

    if not BOT_ACTIVE:
        await update.message.reply_text("⚠️ Bot is OFF. Use /on to activate.")
        return

    try:
        n = int(update.message.text)
    except:
        await update.message.reply_text("❌ Invalid number.")
        return

    if n < 1 or n > 100000:
        await update.message.reply_text("❌ Number must be between 1 and 100000.")
        return

    waiting_for_pickup_number = False

    pure = clean_listA()

    if len(pure) == 0:
        await update.message.reply_text("⚠️ No valid usernames available.")
        return

    winners = random.sample(pure, min(n, len(pure)))

    msg = f"🎉 *PURE Winner List ({len(winners)} Selected)*\n\n"
    for i, w in enumerate(winners, 1):
        msg += f"{i}. `{w}`\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


# ==========================
# START BOT (GSM HOSTING SAFE)
# ==========================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("on", turn_on))
    app.add_handler(CommandHandler("off", turn_off))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_list))

    print("BOT RUNNING...")
    await app.run_polling()


# GSM SAFE LOOP FIX
if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
