import logging
import os

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.notifications import notify_new_borrowing
from borrowings.permissions import IsBorrowerOrAdmin
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingCreateSerializer,
    BorrowingReturnSerializer,
)
from payments.services import StripePaymentService, calculate_amount

stripe_api_key = os.getenv("STRIPE_API_KEY")

logger = logging.getLogger(__name__)

FINE_MULTIPLIER = 2


class BorrowingCreateAPIView(generics.CreateAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create a borrowing",
        responses={201: BorrowingCreateSerializer},
        request=BorrowingCreateSerializer,
    )
    @transaction.atomic
    def perform_create(self, serializer):
        logger.info("Performing create operation...")

        instance = serializer.save()

        if instance.book.inventory < 1:
            raise serializers.ValidationError(
                "Not enough inventory to borrow this book"
            )
        instance.book.inventory -= 1
        instance.book.save()
        logger.info(f"Book inventory updated. New inventory: {instance.book.inventory}")

        payment_service = StripePaymentService()
        payment_data = {
            "user_id": instance.user.id,
            "amount": calculate_amount(instance),
            "book_name": instance.book.title,
        }
        payment_response = payment_service.create_payment_session(payment_data)

        if payment_response["success"]:
            instance.session_id = payment_response["session_id"]
            instance.session_url = payment_response["session_url"]
            instance.save()
            notify_new_borrowing(instance)
            return Response(
                {"borrowing": serializer.data}, status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {"error": "Payment processing failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class BorrowingListAPIView(generics.ListAPIView):
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List borrowings",
        responses={200: BorrowingSerializer(many=True)},
        parameters=[
            {
                "name": "user_id",
                "required": False,
                "in": "query",
                "description": "Filter by user ID",
                "schema": {"type": "integer"},
            },
            {
                "name": "is_active",
                "required": False,
                "in": "query",
                "description": "Filter by active status",
                "schema": {"type": "string", "enum": ["true", "false"]},
            },
        ],
    )
    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        is_active = self.request.query_params.get("is_active")
        queryset = Borrowing.objects.all()

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if is_active:
            is_active_bool = is_active.lower() == "true"
            queryset = queryset.filter(actual_return_date__isnull=is_active_bool)

        return queryset


class BorrowingDetailAPIView(generics.RetrieveAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [IsBorrowerOrAdmin]

    @extend_schema(summary="Retrieve a borrowing", responses={200: BorrowingSerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class BorrowingReturnAPIView(generics.UpdateAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingReturnSerializer
    permission_classes = [IsBorrowerOrAdmin]

    @extend_schema(summary="Return a borrowing", request=BorrowingReturnSerializer)
    def perform_update(self, serializer):
        instance = serializer.save()

        fine_amount = self.calculate_fine_amount(instance)

        if fine_amount > 0:
            instance.fine_paid = True
            instance.save()

        return Response(serializer.data)

    def calculate_fine_amount(self, instance):
        if (
            instance.actual_return_date
            and instance.actual_return_date > instance.expected_return_date
        ):
            overdue_days = (
                instance.actual_return_date - instance.expected_return_date
            ).days

            fine_amount = overdue_days * instance.book.daily_fee * FINE_MULTIPLIER
            return fine_amount
        return 0
