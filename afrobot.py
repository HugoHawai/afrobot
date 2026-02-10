import os
import logging
import asyncio
import json
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
# Chargement / sauvegarde JSON
# -----------------------------

def load_contributions():
    global contributions
    if os.path.exists(CONTRIB_FILE):
        try:
            with open(CONTRIB_FILE, "r", encoding="utf-8") as f:
                contributions = json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement JSON : {e}")
            contributions = {}
    else:
        contributions = {}


def save_contributions():
    try:
        with open(CONTRIB_FILE, "w", encoding="utf-8") as f:
            json.dump(contributions, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erreur sauvegarde JSON : {e}")


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
        await update.message.reply_text("Aucune contribution enregistrée pour le moment.")
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

    text = "🏆 Classement des contributeurs :\n\n" + "\n".join(lines)
    await update.message.reply_text(text)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await update.message.reply_text(f"Tu as dit : {update.message.text}")


# -----------------------------
# Gestion des médias
# -----------------------------

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global OWNER_ID
    message = update.message
    user = message.from_user
    
    # 🔥 Filtrage du canal lié
    if message.forward_from_chat and message.forward_from_chat.id == -1003680135433:
        return


    if OWNER_ID is None:
        OWNER_ID = user.id

    user_id = str(user.id)
    contributions[user_id] = contributions.get(user_id, 0) + 1
    count = contributions[user_id]

    save_contributions()

    try:
        if message.photo:
            file_id = message.photo[-1].file_id
            await context.bot.send_photo(chat_id=OWNER_ID, photo=file_id)

        elif message.video:
            file_id = message.video.file_id
            await context.bot.send_video(chat_id=OWNER_ID, video=file_id)

        elif message.animation:
            file_id = message.animation.file_id
            await context.bot.send_animation(chat_id=OWNER_ID, animation=file_id)

        elif message.document and message.document.mime_type.startswith("video"):
            file_id = message.document.file_id
            await context.bot.send_document(chat_id=OWNER_ID, document=file_id)

    except Exception as e:
        logger.error(f"Erreur en envoyant le média : {e}")

    try:
        await message.delete()
    except Exception as e:
        logger.error(f"Impossible de supprimer le message : {e}")

    try:
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=f"Merci {user.first_name} pour ta {count}ᵉ contribution 🙏"
        )
    except Exception as e:
        logger.error(f"Erreur en envoyant le message de remerciement : {e}")


# -----------------------------
# Webhook + serveur aiohttp
# -----------------------------

async def main():
    load_contributions()

    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN manquant")
    if not WEBHOOK_URL:
        raise SystemExit("WEBHOOK_URL manquant")

    application = Application.builder().token(BOT_TOKEN).updater(None).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    media_filter = (
        filters.PHOTO |
        filters.VIDEO |
        filters.ANIMATION |
        filters.Document.VIDEO
    )
    application.add_handler(MessageHandler(media_filter, handle_media))

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