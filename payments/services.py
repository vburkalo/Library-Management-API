from datetime import datetime, timedelta, date

import stripe
from django.conf import settings


class StripePaymentService:
    def __init__(self, api_key=None):
        self.api_key = api_key or settings.STRIPE_API_KEY
        stripe.api_key = self.api_key

    def create_payment_session(self, payment_data):
        try:
            expiration_time = datetime.now() + timedelta(hours=24)
            expiration_time_unix = int(expiration_time.timestamp())

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "unit_amount": int(payment_data["amount"] * 100),
                            "product_data": {"name": payment_data["book_name"]},
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=settings.STRIPE_SUCCESS_URL,
                cancel_url=settings.STRIPE_CANCEL_URL,
                payment_intent_data={
                    "metadata": {"expiration_time": expiration_time_unix}
                },
            )
            return {
                "success": True,
                "session_id": session.id,
                "session_url": session.url,
            }
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}

    def get_success_url(self):
        return settings.STRIPE_SUCCESS_URL

    def get_cancel_url(self):
        return settings.STRIPE_CANCEL_URL


def calculate_amount(borrowing_instance):
    if borrowing_instance.actual_return_date:
        duration = (
            borrowing_instance.actual_return_date - borrowing_instance.borrow_date
        ).days
    else:
        duration = (date.today() - borrowing_instance.borrow_date).days

    return duration * borrowing_instance.book.daily_fee
