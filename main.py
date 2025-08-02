from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import CallbackContext
from dotenv import load_dotenv
import os


load_dotenv()

TARGET_WORD = ["louis", "l*uis"]
count = 676 # manually retrieved from our chat

async def check_message(update: Update, context: CallbackContext):
    global count
    message = update.message.text.lower()
    
    if any(word in message for word in TARGET_WORD):
        count += 1
    
    if count % 100 == 0 or count == 677:
        update.message.reply_text(f"You have reached the target word count of {count}!")

        chat_id = update.message.chat_id
        await context.bot.send_message(chat_id, f"🎉 Congrats to {update.message.from_user.first_name} for reaching the target word count of 677!")


async def main():
    bot_token = os.getenv('TOKEN')

    application = Application.builder().token(bot_token).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("Bot is running...")

    # Run forever
    await asyncio.Event().wait()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
