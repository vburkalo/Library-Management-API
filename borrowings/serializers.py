from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from borrowings.models import Borrowing
from payments.services import StripePaymentService
from users.models import User
from books.models import Book

FINE_MULTIPLIER = 10


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
        user = attrs.get("user")
        book = attrs.get("book")

        active_borrowings = Borrowing.objects.filter(
            user=user, actual_return_date__isnull=True
        ).count()
        if active_borrowings > 0:
            raise serializers.ValidationError(
                "You already have an active borrowing. Please return the book before borrowing a new one."
            )

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
    user_email = serializers.SerializerMethodField()
    book_details = serializers.SerializerMethodField()
    session_id = serializers.SerializerMethodField()
    session_url = serializers.SerializerMethodField()
    fine_payment_status = serializers.SerializerMethodField()
    fine_amount = serializers.SerializerMethodField()

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
            "session_id",
            "session_url",
            "fine_payment_status",
            "fine_amount",
        ]

    def validate(self, attrs):
        borrow_date = attrs.get("borrow_date")
        expected_return_date = attrs.get("expected_return_date")
        actual_return_date = attrs.get("actual_return_date")
        book = attrs.get("book")

        if (
            expected_return_date < borrow_date
            or borrow_date > expected_return_date
            or actual_return_date < expected_return_date
        ):
            raise serializers.ValidationError(
                "Expected return date or actual return date cannot be sooner than the borrow date"
                " and actual return date cannot be sooner than the expected borrow date."
            )

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

    def get_fine_payment_status(self, obj):
        return obj.fine_payment_status

    def get_fine_amount(self, obj):
        return obj.fine_amount

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)

            if instance.actual_return_date:
                fine_amount = instance.calculate_fine_amount(
                    instance.book.daily_fee, FINE_MULTIPLIER
                )
                if fine_amount > 0:
                    instance.fine_amount = fine_amount
                    instance.fine_payment_status = "pending"
                    instance.save()

                    payment_service = StripePaymentService()
                    payment_data = {
                        "user_id": instance.user.id,
                        "amount": fine_amount,
                        "book_name": instance.book.title,
                    }

                    payment_response = payment_service.create_payment_session(
                        payment_data
                    )

                    if payment_response["success"]:
                        instance.session_id = payment_response["session_id"]
                        instance.session_url = payment_response["session_url"]

                        instance.fine_payment_status = "pending"
                        instance.save()
                    else:
                        raise ValidationError("Fine payment processing failed.")

            return instance
