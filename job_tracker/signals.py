from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import ProfileTarget

# Signal to automatically create a profile target when a user is created
@receiver(post_save, sender=User)
def create_profile_target(sender, instance, created, **kwargs):
    if created:
        ProfileTarget.objects.create(user=instance)