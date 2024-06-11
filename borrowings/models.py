from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone

from books.models import Book
from users.models import User

FINE_MULTIPLIER = 10


class Borrowing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrow_date = models.DateField(default=timezone.now)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(blank=True, null=True)
    payment_status = models.CharField(max_length=20, default="pending")
    fine_payment_status = models.CharField(max_length=20, default="pending")
    session_id = models.CharField(max_length=100, blank=True, null=True)
    session_url = models.CharField(max_length=100, blank=True, null=True)
    amount_paid = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    fine_amount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )

    def is_active(self):
        return self.actual_return_date is None

    def calculate_overdue_days(self):
        if self.actual_return_date and self.actual_return_date > self.expected_return_date:
            return (self.actual_return_date - self.expected_return_date).days
        elif self.actual_return_date and self.actual_return_date <= self.expected_return_date:
            return 0
        elif not self.actual_return_date and timezone.now().date() > self.expected_return_date:
            return (timezone.now().date() - self.expected_return_date).days
        else:
            return 0

    def calculate_fine_amount(self, daily_fee, fine_multiplier):
        overdue_days = self.calculate_overdue_days()
        return overdue_days * daily_fee * fine_multiplier

    def return_book(self):
        if self.actual_return_date > self.expected_return_date:
            fine_amount = self.calculate_fine_amount(
                self.book.daily_fee, FINE_MULTIPLIER
            )
            if fine_amount > 0:
                self.fine_amount = fine_amount
                self.fine_payment_status = "pending"
        self.save()

    def __str__(self):
        return f"{self.user} borrows {self.book}"

    class Meta:
        unique_together = ["user", "book"]


@receiver(pre_delete, sender=Borrowing)
def update_inventory_on_return(sender, instance, **kwargs):
    if instance.actual_return_date is not None:
        instance.book.inventory += 1
        instance.book.save()
