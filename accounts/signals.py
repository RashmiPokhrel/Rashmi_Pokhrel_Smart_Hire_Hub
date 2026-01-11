# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RecruiterProfile, User

@receiver(post_save, sender=User)
def create_recruiter_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'recruiter':
        RecruiterProfile.objects.create(user=instance)
