from django.test import TestCase
from books.models import Author, Book


class AuthorModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Author.objects.create(first_name="John", last_name="Doe")

    def test_author_str_representation(self):
        author = Author.objects.get(id=1)
        expected_str = f"John Doe"
        self.assertEqual(str(author), expected_str)


class BookModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = Author.objects.create(first_name="Jane", last_name="Smith")
        Book.objects.create(
            title="Test Book", cover="HARD", inventory=10, daily_fee=10.50
        )
        Book.objects.get(id=1).authors.add(author)

    def test_book_str_representation(self):
        book = Book.objects.get(id=1)
        expected_str = (
            f"Title: Test Book | Author{'s' if book.authors.count() > 1 else ''}: "
            f"{', '.join([str(author) for author in book.authors.all()])} | "
            f"Cover: {book.get_cover_display()} | Inventory: {book.inventory} | "
            f"Daily Fee: ${book.daily_fee}"
        )
        self.assertEqual(str(book), expected_str)

    def test_book_cover_display(self):
        book = Book.objects.get(id=1)
        self.assertEqual(book.get_cover_display(), "Hardcover")

    def test_book_authors_count(self):
        book = Book.objects.get(id=1)
        self.assertEqual(book.authors.count(), 1)

    def test_book_inventory_positive_integer(self):
        book = Book.objects.get(id=1)
        self.assertGreaterEqual(book.inventory, 0)

    def test_book_daily_fee_decimal_places(self):
        book = Book.objects.get(id=1)
        self.assertEqual(book.daily_fee, 10.50)

    def test_book_daily_fee_max_digits(self):
        book = Book.objects.get(id=1)
        self.assertLessEqual(len(str(book.daily_fee).split(".")[0]), 5)
