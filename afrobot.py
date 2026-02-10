import os
import logging
import asyncio
import json
from datetime import datetime, timedelta
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

CONTRIB_FILE = "contributions.json"

contributions = {}
OWNER_ID = None


# -----------------------------
# JSON
# -----------------------------

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erreur sauvegarde JSON {path}: {e}")


def load_all():
    global contributions
    contributions = load_json(CONTRIB_FILE)


def save_all():
    save_json(CONTRIB_FILE, contributions)


# -----------------------------
# Commandes
# -----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global OWNER_ID
    OWNER_ID = update.effective_user.id
    await update.message.reply_text("AFROBOT opérationnel. Je suis prêt à recevoir les contributions.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commandes : /start /help /top")


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not contributions:
        await update.message.reply_text("Aucune contribution enregistrée.")
        return

    sorted_users = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    lines = []

    for user_id, count in sorted_users[:20]:
        try:
            user = await context.bot.get_chat(int(user_id))
            name = user.first_name
        except:
            name = f"Utilisateur {user_id}"
        lines.append(f"{name} — {count} contributions")

    await update.message.reply_text("🏆 Classement général :\n\n" + "\n".join(lines))


# -----------------------------
# Gestion des médias
# -----------------------------

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global OWNER_ID
    message = update.message
    user = message.from_user

    # Ignorer les messages provenant du canal lié
    if message.forward_from_chat and message.forward_from_chat.id == -1003680135433:
        return

    if OWNER_ID is None:
        OWNER_ID = user.id

    user_id = str(user.id)

    contributions[user_id] = contributions.get(user_id, 0) + 1
    save_all()

    try:
        if message.photo:
            await context.bot.send_photo(chat_id=OWNER_ID, photo=message.photo[-1].file_id)
        elif message.video:
            await context.bot.send_video(chat_id=OWNER_ID, video=message.video.file_id)
        elif message.animation:
            await context.bot.send_animation(chat_id=OWNER_ID, animation=message.animation.file_id)
        elif message.document and message.document.mime_type.startswith("video"):
            await context.bot.send_document(chat_id=OWNER_ID, document=message.document.file_id)
    except Exception as e:
        logger.error(f"Erreur transfert média : {e}")

    try:
        await message.delete()
    except:
        pass

    await context.bot.send_message(
        chat_id=message.chat_id,
        text=f"Merci {user.first_name} pour ta {contributions[user_id]}ᵉ contribution 🙏"
    )


# -----------------------------
# Handler texte (dernier)
# -----------------------------

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await update.message.reply_text(f"Tu as dit : {update.message.text}")


# -----------------------------
# Webhook
# -----------------------------

async def main():
    load_all()

    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN manquant")
    if not WEBHOOK_URL:
        raise SystemExit("WEBHOOK_URL manquant")

    application = Application.builder().token(BOT_TOKEN).updater(None).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("top", top_command))

    media_filter = (
        filters.PHOTO |
        filters.VIDEO |
        filters.ANIMATION |
        filters.Document.VIDEO
    )
    application.add_handler(MessageHandler(media_filter, handle_media))

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

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())