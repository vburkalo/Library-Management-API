from rest_framework import serializers
from borrowings.models import Borrowing
from users.models import User
from books.models import Book


class BorrowingCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    user_email = serializers.SerializerMethodField()
    book_details = serializers.SerializerMethodField()

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "user_email",
            "book_details",
        ]

    def validate(self, attrs):
        book = attrs.get("book")
        if book.inventory <= 0:
            raise serializers.ValidationError(
                "Not enough inventory to borrow this book"
            )
        return attrs

    def get_user_email(self, obj):
        return obj.user.email

    def get_book_details(self, obj):
        book = obj.book
        author_names = [
            f"{author.first_name} {author.last_name}" for author in book.authors.all()
        ]
        return f"{book.title} by {', '.join(author_names)}"


class BorrowingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    book = serializers.SerializerMethodField()

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        ]

    def get_user(self, obj):
        return obj.user.email

    def get_book(self, obj):
        book = obj.book
        author_names = [
            f"{author.first_name} {author.last_name}" for author in book.authors.all()
        ]
        return f"{book.title} by {', '.join(author_names)}"


class BorrowingReturnSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        ]
