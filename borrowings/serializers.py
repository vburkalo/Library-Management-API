from rest_framework import serializers
from borrowings.models import Borrowing
from users.models import User
from books.models import Book


class BorrowingCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    user_email = serializers.SerializerMethodField()
    book_details = serializers.SerializerMethodField()
    session_id = serializers.SerializerMethodField()
    session_url = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()

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
            "payment_status",
            "amount_paid",
            "session_id",
            "session_url",
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

    def get_session_id(self, obj):
        return obj.session_id

    def get_session_url(self, obj):
        return obj.session_url

    def get_payment_status(self, obj):
        return obj.payment_status

    def create(self, validated_data):
        borrow_date = validated_data.get("borrow_date")
        expected_return_date = validated_data.get("expected_return_date")
        book = validated_data.get("book")
        daily_fee = book.daily_fee

        borrow_duration = (expected_return_date - borrow_date).days

        total_fee = borrow_duration * daily_fee

        amount_paid = validated_data.get("amount_paid", 0)
        if amount_paid < total_fee:
            raise serializers.ValidationError(
                "Amount paid should be at least equal to the total fee."
            )

        return super().create(validated_data)


class BorrowingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    book = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "payment_status",
        ]

    def get_user(self, obj):
        return obj.user.email

    def get_book(self, obj):
        book = obj.book
        author_names = [
            f"{author.first_name} {author.last_name}" for author in book.authors.all()
        ]
        return f"{book.title} by {', '.join(author_names)}"

    def get_payment_status(self, obj):
        return obj.payment_status


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
