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

collection = db.collection('count')
DOCUMENT_ID = "count"

# Set to keep track of counts that have already triggered a message
set_once = set()

def is_similar(word):
    similarity = fuzz.ratio(word, TARGET_WORD)
    if similarity >= 80:  
        return True
    return False

def increment_global_count():
    doc_ref = collection.document(DOCUMENT_ID)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        new_count = data.get('count', 0) + 1


    doc_ref.set({'count': new_count})
    return new_count

# Optional: retrieve current count
def get_current_count():
    doc_ref = collection.document(DOCUMENT_ID)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict().get('count', 0)
    return 0

async def fetch_current_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = get_current_count()
    await update.message.reply_text(f"Current count is {count}")

async def check_message(update: Update, context: CallbackContext):
    message = update.message.text.lower()
    hasGacha = False
    for word in message.split():
        if is_similar(word):
            increment_global_count()
            count = get_current_count()
            print(f"Count updated to: {count}")

            if not hasGacha:
                await roll_gacha(update, context)
                hasGacha = True

            if count % 1000 == 0 and count not in set_once:
                chat_id = update.message.chat_id
                await context.bot.send_message(chat_id, f"🎉 RAHHH Congrats to {update.message.from_user.first_name} for reaching the target word count of {count}! You get 1 class part!")
                set_once.add(count)
            elif count % 100 == 0 and count not in set_once:

                chat_id = update.message.chat_id
                await context.bot.send_message(chat_id, f"🎉 Congrats to {update.message.from_user.first_name} for reaching the target word count of {count}!")

                set_once.add(count)

async def roll_gacha(update, context):
    gacha = random.randint(1, 100)
    if gacha == 1:
        chat_id = update.message.chat_id
        try:
            with open("lobsterThermidor.jpg", 'rb') as photo_file:
                await context.bot.send_photo(chat_id, photo_file)
        except Exception as e:
            print(e)
        



async def main():
    bot_token = os.getenv('TOKEN')

    application = Application.builder().token(bot_token).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))
    application.add_handler(CommandHandler("count", fetch_current_count))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("Bot is running...")

    # Run forever
    await asyncio.Event().wait()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
