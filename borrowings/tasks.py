from celery import shared_task
from django.utils import timezone
from borrowings.models import Borrowing
import requests
from django.conf import settings


@shared_task
def check_overdue_borrowings():
    today = timezone.now().date()
    overdue_borrowings = Borrowing.objects.filter(expected_return_date__lte=today, actual_return_date__isnull=True)

    chat_id = settings.TELEGRAM_CHAT_ID
    bot_token = settings.TELEGRAM_BOT_TOKEN
    bot_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    if overdue_borrowings.exists():
        for borrowing in overdue_borrowings:
            message = (
                f"Borrowing ID: {borrowing.id} is overdue.\n"
                f"User: {borrowing.user.email}\n"
                f"Book: {borrowing.book.title}\n"
                f"Expected return date: {borrowing.expected_return_date}"
            )
            requests.post(bot_url, data={"chat_id": chat_id, "text": message})
    else:
        requests.post(bot_url, data={"chat_id": chat_id, "text": "No borrowings overdue today!"})
