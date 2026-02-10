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


# --- Handlers de base ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Salut, je suis AFROBOT (PTB 21.6, polling).")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Commandes dispo : /start /help")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.text:
        await update.message.reply_text(f"Tu as dit : {update.message.text}")


# --- Fonction principale ---

async def main() -> None:
    if not BOT_TOKEN:
        logger.error("La variable d'environnement BOT_TOKEN n'est pas définie.")
        raise SystemExit("BOT_TOKEN manquant")

    application = Application.builder().token(BOT_TOKEN).build()

    # Ajout des handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Lancement en polling (simple, robuste sur Render)
    await application.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())