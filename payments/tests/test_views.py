from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from borrowings.models import Borrowing, Book
import datetime

User = get_user_model()


class StripePaymentSuccessAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test_user@gmail.com", password="12345678"
        )
        self.client.force_authenticate(
            user=self.user
        )
        self.book = Book.objects.create(title="Test Book", inventory=10, daily_fee=5)
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            session_id="test_session_id",
            expected_return_date=datetime.date.today(),
            book_id=self.book.id,
        )

    def test_payment_success(self):
        url = reverse("payment_success")
        response = self.client.get(url, {"session_id": "test_session_id"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.borrowing.refresh_from_db()
        self.assertEqual(self.borrowing.payment_status, "paid")
        self.assertIsNotNone(self.borrowing.actual_return_date)

    def test_payment_success_missing_session_id(self):
        url = reverse("payment_success")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StripePaymentCancelAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test_user@gmail.com", password="12345678"
        )
        self.client.force_authenticate(
            user=self.user
        )
        self.book = Book.objects.create(title="Test Book", inventory=10, daily_fee=5)
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            session_id="test_session_id",
            expected_return_date=datetime.date.today(),
            book_id=self.book.id,
        )

    def test_payment_cancel(self):
        url = reverse("payment_cancel")
        response = self.client.get(url, {"session_id": "test_session_id"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.borrowing.refresh_from_db()
        self.assertEqual(self.borrowing.payment_status, "cancelled")

    def test_payment_cancel_missing_session_id(self):
        url = reverse("payment_cancel")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
