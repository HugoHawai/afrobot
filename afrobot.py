import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # ex: https://afrobot-wbuk.onrender.com
PORT = int(os.environ.get("PORT", "10000"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut, je suis AFROBOT (webhook manuel PTB 21.6).")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commandes dispo : /start /help")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await update.message.reply_text(f"Tu as dit : {update.message.text}")


async def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN manquant")
    if not WEBHOOK_URL:
        raise SystemExit("WEBHOOK_URL manquant")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    await application.initialize()
    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")

    await application.start()

    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
    )

    await application.updater.idle()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())