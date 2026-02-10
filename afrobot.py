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

# --- Logging propre ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Récupération des variables d'environnement ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_URL")  # ex: https://afrobot.onrender.com
PORT = int(os.environ.get("PORT", "10000"))       # Render fournit PORT


# --- Handlers de base (à adapter avec ta logique plus tard) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Salut, je suis AFROBOT (version PTB 20, webhook Render).")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Commande dispo : /start /help")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Répond simplement avec le même texte
    if update.message and update.message.text:
        await update.message.reply_text(f"Tu as dit : {update.message.text}")


# --- Fonction principale ---

async def main() -> None:
    if not BOT_TOKEN:
        logger.error("La variable d'environnement BOT_TOKEN n'est pas définie.")
        raise SystemExit("BOT_TOKEN manquant")

    if not WEBHOOK_BASE_URL:
        logger.error("La variable d'environnement WEBHOOK_URL n'est pas définie.")
        raise SystemExit("WEBHOOK_URL manquant (ex: https://afrobot.onrender.com)")

    application = Application.builder().token(BOT_TOKEN).build()

    # Ajout des handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # URL complète du webhook
    webhook_url = f"{WEBHOOK_BASE_URL}/webhook"

    logger.info(f"Configuration du webhook sur : {webhook_url}")
    # Lancement du serveur webhook intégré à PTB
    await application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=webhook_url,
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())