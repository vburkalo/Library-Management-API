from datetime import date, timedelta
from unittest import mock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from books.models import Book
from borrowings.models import Borrowing
from users.models import User


class BorrowingAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="testuser@example.com", password="testpass"
        )
        self.client.force_authenticate(user=self.user)

        self.book = Book.objects.create(
            title="Hamlet",
            daily_fee=10,
            inventory=5,
        )

        self.borrowing_url = reverse("borrowing-create")
        self.borrowing_list_url = reverse("borrowing-list")
        self.borrowing_return_url = lambda pk: reverse(
            "borrowing-return", kwargs={"pk": pk}
        )
        self.borrowing_detail_url = lambda pk: reverse(
            "borrowing-detail", kwargs={"pk": pk}
        )

    @mock.patch("payments.services.StripePaymentService.create_payment_session")
    def test_create_borrowing(self, mock_create_payment_session):
        mock_create_payment_session.return_value = {
            "success": True,
            "session_id": "test_session_id",
            "session_url": "https://test_url.com",
        }

        data = {
            "user": self.user.id,
            "book": self.book.id,
            "borrow_date": date.today(),
            "expected_return_date": date.today() + timedelta(days=1),
            "amount_paid": 10,
        }

        response = self.client.post(self.borrowing_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Borrowing.objects.count(), 1)
        borrowing = Borrowing.objects.first()
        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(borrowing.book, self.book)
        self.assertEqual(borrowing.session_id, "test_session_id")
        self.assertEqual(borrowing.session_url, "https://test_url.com")

    def test_list_borrowings(self):
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=1),
            actual_return_date=None,
        )

        response = self.client.get(self.borrowing_list_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_borrowing_detail(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=1),
            actual_return_date=None,
        )

        response = self.client.get(
            self.borrowing_detail_url(borrowing.id), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], borrowing.id)

    @mock.patch("payments.services.calculate_amount", return_value=40)
    def test_return_borrowing(self, mock_calculate_amount):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today() - timedelta(days=5),
            expected_return_date=date.today() - timedelta(days=3),
            actual_return_date=None,
        )

        data = {"actual_return_date": date.today()}

        response = self.client.patch(
            self.borrowing_return_url(borrowing.id), data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.assertEqual(borrowing.actual_return_date, date.today())
        self.assertEqual(borrowing.fine_amount, 300)
        self.assertEqual(borrowing.fine_payment_status, "pending")

    @mock.patch(
        "payments.services.StripePaymentService.create_payment_session",
        return_value={
            "success": True,
            "session_id": "test_session_id",
            "session_url": "https://test_url.com",
        },
    )
    def test_borrowing_date_validation(self, mock_create_payment_session):
        data = {
            "user": self.user.id,
            "book": self.book.id,
            "borrow_date": date.today(),
            "expected_return_date": date.today() - timedelta(days=5),
            "amount_paid": 10,
        }
        response = self.client.post(self.borrowing_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Expected return date cannot be before borrow date.", str(response.data)
        )

    def test_active_borrowing_validation(self):
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=1),
            actual_return_date=None,
        )

        data = {
            "user": self.user.id,
            "book": self.book.id,
            "borrow_date": date.today(),
            "expected_return_date": date.today() + timedelta(days=1),
            "amount_paid": 10,
        }

        response = self.client.post(self.borrowing_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "The fields user, book must make a unique set.", str(response.data)
        )
