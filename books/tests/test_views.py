from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from django.urls import reverse
from books.models import Author, Book
from books.serializers import AuthorSerializer, BookSerializer


class AuthorViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@gmail.com", password="password"
        )
        self.client.force_authenticate(user=self.user)
        self.author1 = Author.objects.create(first_name="John", last_name="Doe")
        self.author2 = Author.objects.create(first_name="Jane", last_name="Smith")

    def test_author_list(self):
        response = self.client.get(reverse("author-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        authors = Author.objects.all()
        serializer = AuthorSerializer(authors, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_author_detail(self):
        response = self.client.get(reverse("author-detail", args=[self.author1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        author = Author.objects.get(id=self.author1.id)
        serializer = AuthorSerializer(author)
        self.assertEqual(response.data, serializer.data)


class BookViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@gmail.com", password="password"
        )
        self.client.force_authenticate(user=self.user)
        self.author1 = Author.objects.create(first_name="John", last_name="Doe")
        self.author2 = Author.objects.create(first_name="Jane", last_name="Smith")
        self.book1 = Book.objects.create(
            title="Test Book 1", cover="HARD", inventory=10, daily_fee="10.50"
        )
        self.book2 = Book.objects.create(
            title="Test Book 2", cover="SOFT", inventory=5, daily_fee="8.99"
        )

    def test_book_list(self):
        response = self.client.get(reverse("book-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_book_detail(self):
        response = self.client.get(reverse("book-detail", args=[self.book1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        book = Book.objects.get(id=self.book1.id)
        serializer = BookSerializer(book)
        self.assertEqual(response.data, serializer.data)
