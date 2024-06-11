from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from users.models import User
from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingCreateSerializer, BorrowingReturnSerializer


class BorrowingCreateSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@example.com")
        self.book = Book.objects.create(title="Test Book", inventory=1, daily_fee=1.0)
        self.data = {
            "user": self.user.id,
            "book": self.book.id,
            "borrow_date": timezone.now().date(),
            "expected_return_date": timezone.now().date() + timezone.timedelta(days=7),
            "actual_return_date": None,
            "amount_paid": 7.0,
        }

    def test_validate_active_borrowings(self):
        # Create an active borrowing for the user
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=7),
        )
        serializer = BorrowingCreateSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_validate_inventory(self):
        self.book.inventory = 0
        self.book.save()
        serializer = BorrowingCreateSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_create(self):
        serializer = BorrowingCreateSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        borrowing = serializer.save()
        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(borrowing.book, self.book)


class BorrowingReturnSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@example.com")
        self.book = Book.objects.create(title="Test Book", inventory=1, daily_fee=1.0)
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=7),
        )
        self.data = {
            "borrow_date": timezone.now().date(),
            "expected_return_date": timezone.now().date() + timezone.timedelta(days=7),
            "actual_return_date": None,
            "book": self.book.id,
            "user": self.user.id,
        }

    def test_validate_inventory(self):
        self.book.inventory = 0
        self.book.save()
        serializer = BorrowingReturnSerializer(instance=self.borrowing, data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_update_without_actual_return_date(self):
        self.data["actual_return_date"] = None
        serializer = BorrowingReturnSerializer(instance=self.borrowing, data=self.data)
        self.assertTrue(serializer.is_valid())
        borrowing = serializer.save()
        self.assertIsNone(borrowing.fine_payment_status)
