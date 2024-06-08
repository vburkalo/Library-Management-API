import logging
from django.db import transaction
from rest_framework import generics, serializers
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingCreateSerializer, BorrowingReturnSerializer

logger = logging.getLogger(__name__)


class BorrowingCreateAPIView(generics.CreateAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingCreateSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        logger.info("Performing create operation...")

        instance = serializer.save()
        if instance.book.inventory < 1:
            raise serializers.ValidationError("Not enough inventory to borrow this book")

        instance.book.inventory -= 1
        instance.book.save()
        logger.info(f"Book inventory updated. New inventory: {instance.book.inventory}")


class BorrowingListAPIView(generics.ListAPIView):
    serializer_class = BorrowingSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        is_active = self.request.query_params.get('is_active')
        queryset = Borrowing.objects.all()

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if is_active:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(actual_return_date__isnull=is_active_bool)

        return queryset


class BorrowingDetailAPIView(generics.RetrieveAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer


class BorrowingReturnAPIView(generics.UpdateAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingReturnSerializer

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.actual_return_date:
            instance.book.inventory += 1
            instance.book.save()
