from django.test import TestCase
from books.models import Author, Book
from books.serializers import AuthorSerializer, BookSerializer


class AuthorSerializerTest(TestCase):
    def setUp(self):
        self.author_data = {"id": 1, "first_name": "John", "last_name": "Doe"}
        self.author = Author.objects.create(**self.author_data)
        self.serializer = AuthorSerializer(instance=self.author)

    def test_author_serializer_contains_expected_fields(self):
        data = self.serializer.data
        self.assertEqual(set(data.keys()), set(["id", "first_name", "last_name"]))

    def test_author_serializer_content(self):
        data = self.serializer.data
        self.assertEqual(data["id"], self.author_data["id"])
        self.assertEqual(data["first_name"], self.author_data["first_name"])
        self.assertEqual(data["last_name"], self.author_data["last_name"])


class BookSerializerTest(TestCase):
    def setUp(self):
        self.author1 = Author.objects.create(first_name="John", last_name="Doe")
        self.author2 = Author.objects.create(first_name="Jane", last_name="Smith")
        self.book_data = {
            "id": 1,
            "title": "Test Book",
            "cover": "HARD",
            "inventory": 10,
            "daily_fee": "10.50",
        }
        self.book = Book.objects.create(**self.book_data)
        self.book.authors.add(self.author1, self.author2)
        self.serializer = BookSerializer(instance=self.book)

    def test_book_serializer_contains_expected_fields(self):
        data = self.serializer.data
        self.assertEqual(
            set(data.keys()),
            set(
                [
                    "id",
                    "title",
                    "authors",
                    "author_names",
                    "cover",
                    "inventory",
                    "daily_fee",
                ]
            ),
        )

    def test_book_serializer_content(self):
        data = self.serializer.data
        self.assertEqual(data["id"], self.book_data["id"])
        self.assertEqual(data["title"], self.book_data["title"])
        self.assertEqual(data["cover"], self.book_data["cover"])
        self.assertEqual(data["inventory"], self.book_data["inventory"])
        self.assertEqual(data["daily_fee"], self.book_data["daily_fee"])
        self.assertEqual(set(data["authors"]), set([self.author1.id, self.author2.id]))
