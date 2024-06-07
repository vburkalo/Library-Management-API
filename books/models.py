from django.db import models


class Author(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Book(models.Model):
    COVER_CHOICES = [
        ('HARD', 'Hardcover'),
        ('SOFT', 'Softcover'),
    ]

    title = models.CharField(max_length=255)
    authors = models.ManyToManyField(Author)
    cover = models.CharField(max_length=4, choices=COVER_CHOICES)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        authors = ', '.join([str(author) for author in self.authors.all()])
        author_label = "Author" if self.authors.count() == 1 else "Authors"
        return (
            f"Title: {self.title} | {author_label}: {authors} | "
            f"Cover: {self.get_cover_display()} | Inventory: {self.inventory} | "
            f"Daily Fee: ${self.daily_fee}"
        )
