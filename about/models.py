from django.db import models

# Create your models here.


class About(models.Model):
    """
    Stores a single about us text.
    """
    title = models.CharField(max_length=200)
    content = models.TextField()

    def __str__(self):
        return self.title
