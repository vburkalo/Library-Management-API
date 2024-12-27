from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from borrowings.models import Borrowing
import logging

logger = logging.getLogger(__name__)


class StripePaymentSuccessAPIView(APIView):
    def get(self, request):
        session_id = request.GET.get("session_id")
        if not session_id:
            return Response(
                {"error": "Session ID not provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        borrowing = get_object_or_404(Borrowing, session_id=session_id)
        borrowing.payment_status = "paid"
        borrowing.actual_return_date = timezone.now()
        borrowing.save()

        return Response(
            {"message": "Payment successful", "borrowing": borrowing.id},
            status=status.HTTP_200_OK,
        )


class StripePaymentCancelAPIView(APIView):
    def get(self, request):
        session_id = request.GET.get("session_id")
        if not session_id:
            return Response(
                {"error": "Session ID not provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrowing = get_object_or_404(Borrowing, session_id=session_id)
        borrowing.payment_status = "cancelled"
        borrowing.save()

        return Response(
            {"message": "Payment cancelled", "borrowing": borrowing.id},
            status=status.HTTP_200_OK,
        )
