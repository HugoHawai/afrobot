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
from aiohttp import web

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", "10000"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut, je suis AFROBOT (webhook stable).")


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

    application = Application.builder().token(BOT_TOKEN).updater(None).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    await application.initialize()

    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")

    await application.start()

    async def handle(request):
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.update_queue.put(update)
        return web.Response()

    app = web.Application()
    app.router.add_post("/webhook", handle)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # NE RIEN FERMER : laisser tourner
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())