from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.ext import CallbackContext
from dotenv import load_dotenv
import os
import random
import json
import tempfile
from google.cloud import firestore
from rapidfuzz import fuzz

load_dotenv()

TARGET_WORD = "louis"

firebase_json = os.getenv("FIREBASE_CREDENTIALS")

with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
    tmp_file.write(firebase_json.encode())
    tmp_path = tmp_file.name

# Tell the Firestore SDK where to find credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp_path
db = firestore.Client()

count_collection = db.collection('count')
COUNT_DOCUMENT_ID = "count"

# Set to keep track of counts that have already triggered a message
set_once = set()

def is_similar(word):
    similarity = fuzz.ratio(word, TARGET_WORD)
    if similarity >= 80:  
        return True
    return False

def increment_global_count():
    doc_ref = count_collection.document(COUNT_DOCUMENT_ID)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        new_count = data.get('count', 0) + 1


    doc_ref.set({'count': new_count})
    return new_count

# Optional: retrieve current count
def get_current_count():
    doc_ref = count_collection.document(COUNT_DOCUMENT_ID)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict().get('count', 0)
    return 0

async def fetch_current_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = get_current_count()
    await update.message.reply_text(f"Current count is {count}")

async def check_message(update: Update, context: CallbackContext):
    message = update.message.text.lower()
    for word in message.split():
        if is_similar(word):
            increment_global_count()
            count = get_current_count()
            print(f"Count updated to: {count}")

            await roll_gacha(update, context)

            if count % 1000 == 0 and count not in set_once:
                chat_id = update.message.chat_id
                await context.bot.send_message(chat_id, f"🎉 RAHHH Congrats to {update.message.from_user.first_name} for reaching the target word count of {count}! You get 1 class part!")
                set_once.add(count)
            elif count % 100 == 0 and count not in set_once:

                chat_id = update.message.chat_id
                await context.bot.send_message(chat_id, f"🎉 Congrats to {update.message.from_user.first_name} for reaching the target word count of {count}!")

                set_once.add(count)

gacha_collection = db.collection('gacha')
GACHA_DOCUMENT_ID = "leaderboard"

def increment_leaderboard(update):
    user_id = update.message.from_user.id
    name = update.message.from_user.first_name
    gacha_doc_ref = gacha_collection.document(user_id)
    gacha_doc = gacha_doc_ref.get()

    if gacha_doc.exists:
        gacha_doc_ref.update({"count": firestore.Increment(1)})
        gacha_user_dict = gacha_doc.to_dict()
        if gacha_user_dict["name"] != name:
            gacha_doc_ref.update({"name": name})
    else:
        new_data = {"count": 1, "name": name}
        gacha_doc_ref.set(new_data)

async def fetch_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = gacha_collection.order_by("count", direction=firestore.Query.DESCENDING)
    lb = query.stream()

    lb_msg = "--GACHA LEADERBOARD--\n\n"
    placing = 1
    for user_id in lb:
        user_dict = user_id.to_dict()
        lb_msg += f"#{placing}. {user_dict.name}: {user_dict.count}"
        if placing == 1:
            lb_msg += " 🏆\n"
        else:
            lb_msg += "\n"
        placing += 1
    await update.message.reply_text(lb_msg.rstrip())

async def roll_gacha(update, context):
    gacha = random.randint(1, 100)
    if gacha >= 1:
        chat_id = update.message.chat_id
        try:
            with open("lobsterThermidor.jpg", 'rb') as photo_file:
                await context.bot.send_photo(chat_id, photo_file)
            increment_leaderboard(update)
        except Exception as e:
            print(e)
        



async def main():
    bot_token = os.getenv('TOKEN')

    application = Application.builder().token(bot_token).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))
    application.add_handler(CommandHandler("count", fetch_current_count))
    application.add_handler(CommandHandler("lb", fetch_leaderboard))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("Bot is running...")

    # Run forever
    await asyncio.Event().wait()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
