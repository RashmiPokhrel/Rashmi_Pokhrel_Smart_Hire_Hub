from django.db import models
from django.utils import timezone
from accounts.models import RecruiterProfile, JobSeekerProfile


class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive'),
    ]
    
    # Basic Information
    recruiter = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE, related_name='jobs')
    job_title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    
    # Salary Information
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Additional Information
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    benefits = models.TextField(blank=True, null=True)
    
    # Dates
    expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'jobs'
        ordering = ['-created_at']
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
    
    def __str__(self):
        return f"{self.job_title} - {self.recruiter.company_name}"
    
    def is_expired(self):
        return timezone.now().date() > self.expiry_date
    
    def mark_inactive_if_expired(self):
        """
        Mark this job as inactive if it has passed its expiry date.
        Returns True if the job was updated, False otherwise.
        """
        if self.is_expired() and self.is_active:
            self.is_active = False
            self.save(update_fields=['is_active'])
            return True
        return False
    
    @classmethod
    def mark_all_expired_inactive(cls):
        """
        Mark all expired jobs as inactive.
        Returns the number of jobs updated.
        """
        today = timezone.now().date()
        updated_count = cls.objects.filter(
            expiry_date__lt=today,
            is_active=True
        ).update(is_active=False)
        return updated_count
    
    @classmethod
    def get_active_jobs(cls, recruiter=None):
        """
        Get all active jobs (not expired and is_active=True).
        Optionally filter by recruiter.
        """
        today = timezone.now().date()
        queryset = cls.objects.filter(
            is_active=True,
            expiry_date__gte=today
        )
        if recruiter:
            queryset = queryset.filter(recruiter=recruiter)
        return queryset


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
    ]
    
    # Relationships
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='applications')
    
    # Application Details
    resume = models.FileField(upload_to='resumes/%Y/%m/%d/', blank=True, null=True)
    cover_letter = models.TextField(blank=True, null=True)
    
    # Status and Dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional Notes (for recruiter)
    notes = models.TextField(blank=True, null=True, help_text="Internal notes about this application")
    
    class Meta:
        app_label = 'jobs'
        ordering = ['-applied_date']
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
        unique_together = ['job', 'candidate']  # Prevent duplicate applications
    
    def __str__(self):
        return f"{self.candidate.full_name or self.candidate.user.username} - {self.job.job_title}"
    
    def get_status_display_class(self):
        """Return CSS class for status badge"""
        status_classes = {
            'pending': 'status-pending',
            'reviewed': 'status-reviewed',
            'shortlisted': 'status-shortlisted',
            'rejected': 'status-rejected',
            'accepted': 'status-accepted',
        }
        return status_classes.get(self.status, 'status-pending')
