from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import CallbackContext
from dotenv import load_dotenv
import os


load_dotenv()

TARGET_WORD = ["louis", "l*uis"]
count = 676 # manually retrieved from our chat

set_once = set()
async def check_message(update: Update, context: CallbackContext):
    global count
    message = update.message.text.lower()
    for word in message.split():
        if word in TARGET_WORD:
            count += 1
            print(f"Count updated to: {count}")
            if count % 1000 == 0 and count not in set_once:
                chat_id = update.message.chat_id
                await context.bot.send_message(chat_id, f"🎉 RAHHH Congrats to {update.message.from_user.first_name} for reaching the target word count of {count}! You get 1 class part!")
                set_once.add(count)
            elif count % 100 == 0 and count not in set_once:

                chat_id = update.message.chat_id
                await context.bot.send_message(chat_id, f"🎉 Congrats to {update.message.from_user.first_name} for reaching the target word count of {count}!")

                set_once.add(count)


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
