from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from books.models import Book
from borrowings.models import Borrowing
from payments.services import StripePaymentService
from users.models import User

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
        borrow_date = attrs.get("borrow_date")
        expected_return_date = attrs.get("expected_return_date")

        if expected_return_date < borrow_date:
            raise serializers.ValidationError(
                "Expected return date cannot be before borrow date."
            )

        active_borrowings = Borrowing.objects.filter(
            user=user, actual_return_date__isnull=True
        ).count()
        if active_borrowings > 0:
            raise serializers.ValidationError("You already have an active borrowing.")

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
        with transaction.atomic():
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

            validated_data["amount_paid"] = total_fee

            book.inventory -= 1
            book.save()

            borrowing = super().create(validated_data)

            payment_service = StripePaymentService()
            payment_data = {
                "user_id": borrowing.user.id,
                "amount": total_fee,
                "book_name": borrowing.book.title,
            }

            payment_response = payment_service.create_payment_session(payment_data)
            if payment_response["success"]:
                borrowing.session_id = payment_response["session_id"]
                borrowing.session_url = payment_response["session_url"]
                borrowing.payment_status = "pending"
                borrowing.save()
            else:
                raise ValidationError("Payment processing failed.")

            return borrowing


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
        validators = []

    def validate(self, data):
        user = data.get("user")
        book = data.get("book")
        if Borrowing.objects.filter(
            user=user, book=book, actual_return_date__isnull=True
        ).exists():
            raise ValidationError("You already have an active borrowing")
        return data

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

    def validate(self, data):
        borrowing = self.instance
        actual_return_date = data.get("actual_return_date")

        if actual_return_date:
            if actual_return_date < borrowing.borrow_date:
                raise ValidationError(
                    "Actual return date cannot be before borrow date."
                )
            if (
                borrowing.expected_return_date
                and actual_return_date < borrowing.expected_return_date
            ):
                raise ValidationError(
                    "Actual return date cannot be before expected return date."
                )

        return data

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
