from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from books.models import Book, Author
from books.serializers import BookSerializer, AuthorSerializer


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
