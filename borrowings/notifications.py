import asyncio
from telegram import Bot
from django.conf import settings


async def send_notification(chat_id, message):
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=chat_id, text=message)


def notify_new_borrowing(borrowing):
    chat_id = "6976462510"
    message = f"New borrowing created: {borrowing}"
    asyncio.run(send_notification(chat_id, message))
