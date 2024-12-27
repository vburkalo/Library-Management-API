from django.urls import path
from payments.views import StripePaymentSuccessAPIView, StripePaymentCancelAPIView

urlpatterns = [
    path("success/", StripePaymentSuccessAPIView.as_view(), name="payment_success"),
    path("cancel/", StripePaymentCancelAPIView.as_view(), name="payment_cancel"),
]
