from django.test import TestCase
from django.utils import timezone
from django.db.utils import IntegrityError

from books.models import Book
from users.models import User
from borrowings.models import Borrowing


class BorrowingModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@example.com")
        self.book = Book.objects.create(title="Test Book", inventory=1, daily_fee=1.0)
        self.borrow_date = timezone.now().date()
        self.expected_return_date = self.borrow_date + timezone.timedelta(days=7)

    def test_borrowing_creation(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=self.borrow_date,
            expected_return_date=self.expected_return_date,
        )
        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(borrowing.book, self.book)
        self.assertEqual(borrowing.borrow_date, self.borrow_date)
        self.assertEqual(borrowing.expected_return_date, self.expected_return_date)
        self.assertTrue(borrowing.is_active())

    def test_return_book(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=self.borrow_date,
            expected_return_date=self.borrow_date - timezone.timedelta(days=1),
        )
        # Return the book
        borrowing.actual_return_date = self.borrow_date
        borrowing.save()
        self.assertFalse(borrowing.is_active())

    def test_cannot_create_duplicate_borrowing(self):
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=self.borrow_date,
            expected_return_date=self.expected_return_date,
        )
        with self.assertRaises(IntegrityError):
            Borrowing.objects.create(
                user=self.user,
                book=self.book,
                borrow_date=self.borrow_date,
                expected_return_date=self.expected_return_date,
            )

    def test_calculate_overdue_days(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=self.borrow_date,
            expected_return_date=self.borrow_date - timezone.timedelta(days=1),
        )
        self.assertEqual(borrowing.calculate_overdue_days(), 1)
