import json
import logging
from pathlib import Path
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler, CallbackContext

# === CONFIGURATION ===
BOT_TOKEN = "8382123925:AAGlewNcDU7XPbBdTXWbHtmhXbionR5WQNQ"
ADMIN_ID = 8309817252
GROUP_ID = -1003840984612
CHANNEL_ID = -1003680135433
SCORES_FILE = Path("scores.json")
WEBHOOK_URL = "https://afrobot-ccfa.onrender.com/webhook"
# =====================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)

# Flask app
app = Flask(__name__)

# Dispatcher
dispatcher = Dispatcher(bot, None, workers=4)


# === GESTION SCORES ===
def load_scores():
    if SCORES_FILE.exists():
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_scores(scores):
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)


# === COMMANDES ===
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(f"Salut {user.first_name} ! Ton ID est : {user.id}")


def add_score(update: Update, context: CallbackContext):
    scores = load_scores()
    args = context.args

    if not args:
        update.message.reply_text("Utilisation : /addscore ID_DU_CONTRIBUTEUR")
        return

    user_id = args[0]
    scores[user_id] = scores.get(user_id, 0) + 1
    save_scores(scores)

    update.message.reply_text(f"Score mis à jour pour {user_id} : {scores[user_id]}")


def top(update: Update, context: CallbackContext):
    scores = load_scores()

    if not scores:
        update.message.reply_text("Aucun score pour l'instant.")
        return

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    lines = [f"{i+1}. ID {uid} → {score}" for i, (uid, score) in enumerate(sorted_scores[:10])]

    update.message.reply_text("🏆 Top contributeurs :\n" + "\n".join(lines))


# === GESTION MÉDIAS DU GROUPE ===
def handle_group_media(update: Update, context: CallbackContext):
    message = update.effective_message
    user = message.from_user

    # Forward du média
    try:
        bot.forward_message(
            chat_id=ADMIN_ID,
            from_chat_id=message.chat_id,
            message_id=message.message_id
        )
    except Exception as e:
        logger.error(f"Erreur lors du forward : {e}")

    # Message d'information
    try:
        bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Média envoyé par @{user.username or user.first_name} (ID: {user.id})"
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message admin : {e}")

    # Suppression du message dans le groupe
    try:
        bot.delete_message(
            chat_id=message.chat_id,
            message_id=message.message_id
        )
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du message : {e}")

    # 🔥 Incrémentation automatique du score
    try:
        scores = load_scores()
        uid = str(user.id)
        scores[uid] = scores.get(uid, 0) + 1
        save_scores(scores)
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du score : {e}")

    # Message de remerciement dans le groupe
    try:
        bot.send_message(
            chat_id=message.chat_id,
            text=f"Merci {user.first_name} pour ta contribution ! 🙏"
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message de remerciement : {e}")


# === ROUTE WEBHOOK ===
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200


# === SETUP WEBHOOK ===
@app.route("/")
def index():
    bot.set_webhook(WEBHOOK_URL)
    return "Webhook installé", 200


# === HANDLERS ===
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("addscore", add_score))
dispatcher.add_handler(CommandHandler("top", top))

dispatcher.add_handler(MessageHandler(
    Filters.chat(GROUP_ID) & (Filters.photo | Filters.video | Filters.document),
    handle_group_media
))


# === MAIN ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)