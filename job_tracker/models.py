from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

# Create your models here.


class JobType(models.Model):
    """
    Stores a single job type.
    """
    name = models.CharField(max_length=100, unique=True)
    credits = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.credits} credits)"


class CompletedJob(models.Model):
    """
    Stores a single completed job type entry from :model: `Jobtype`
    related to :model:`auth.User`.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job_type = models.ForeignKey(JobType, on_delete=models.CASCADE)
    completed_on = models.DateField()

    class Meta:
        ordering = ["-completed_on"]

    def __str__(self):
        return f"{self.job_type.credits} credits"


class Absence(models.Model):
    """
    Stores a single absence entry related to :model:`auth.User`.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    duration = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user} absent for {self.duration} hours on {self.date}"


class ProfileTarget(models.Model):
    """
    Stores daily target, hours and rostered days off
    related to :model:`auth.User`.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    daily_target = models.DecimalField(
        max_digits=3, decimal_places=2, default=4.25)
    daily_hours = models.DecimalField(
        max_digits=4, decimal_places=2, default=8.00)

    # PostgreSQL specific model field, ArrayField.
    DAYS_OF_WEEK = [
        ("Mon", "Monday"),
        ("Tue", "Tuesday"),
        ("Wed", "Wednesday"),
        ("Thu", "Thursday"),
        ("Fri", "Friday"),
        ("Sat", "Saturday"),
        ("Sun", "Sunday"),
    ]
    days_off = ArrayField(
        models.CharField(max_length=3, choices=DAYS_OF_WEEK), default=list)

    def __str__(self):
        return f"Engineer:{self.user}, Target:{self.daily_target}"
