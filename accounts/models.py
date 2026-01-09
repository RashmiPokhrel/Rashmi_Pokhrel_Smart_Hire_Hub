from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import timedelta
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ('job_seeker', 'Job Seeker'),
        ('recruiter', 'Recruiter'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)


class JobSeekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(
        upload_to='profiles/',
        default=True,
        blank=True
    )



class RecruiterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    company_email = models.EmailField()
    company_phone = models.CharField(max_length=20)
    company_address = models.TextField()
    profile_image = models.ImageField(upload_to='profiles/', default='profiles/default.png')


class PasswordResetOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)
