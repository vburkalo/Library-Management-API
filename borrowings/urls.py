from django.urls import path
from borrowings.views import (
    BorrowingCreateAPIView,
    BorrowingListAPIView,
    BorrowingDetailAPIView,
    BorrowingReturnAPIView,
)

urlpatterns = [
    path("", BorrowingListAPIView.as_view(), name="borrowing-list"),
    path("<int:pk>/", BorrowingDetailAPIView.as_view(), name="borrowing-detail"),
    path("<int:pk>/return/", BorrowingReturnAPIView.as_view(), name="borrowing-return"),
    path("create/", BorrowingCreateAPIView.as_view(), name="borrowing-create"),
]
