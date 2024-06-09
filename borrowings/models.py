from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone

from books.models import Book
from users.models import User


class Borrowing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrow_date = models.DateField(default=timezone.now)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(blank=True, null=True)
    payment_status = models.CharField(max_length=20, default="pending")
    session_id = models.CharField(max_length=100, blank=True, null=True)
    session_url = models.CharField(max_length=100, blank=True, null=True)
    amount_paid = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )

    def is_active(self):
        return self.actual_return_date is None

    def __str__(self):
        return f"{self.user} borrows {self.book}"


@receiver(pre_delete, sender=Borrowing)
def update_inventory_on_return(sender, instance, **kwargs):
    if instance.actual_return_date is not None:
        instance.book.inventory += 1
        instance.book.save()
