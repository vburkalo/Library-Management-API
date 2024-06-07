from rest_framework import serializers
from books.models import Author, Book


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'first_name', 'last_name')


class BookSerializer(serializers.ModelSerializer):
    authors = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), many=True)
    author_names = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ('id', 'title', 'authors', 'author_names', 'cover', 'inventory', 'daily_fee')

    def get_author_names(self, obj):
        return ', '.join([f"{author.first_name} {author.last_name}" for author in obj.authors.all()])
