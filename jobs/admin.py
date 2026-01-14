from django.contrib import admin
from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'recruiter', 'location', 'job_type', 'is_active', 'expiry_date', 'created_at')
    list_filter = ('job_type', 'experience_level', 'is_active', 'created_at', 'expiry_date')
    search_fields = ('job_title', 'location', 'recruiter__company_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('recruiter', 'job_title', 'description', 'location', 'job_type')
        }),
        ('Salary Information', {
            'fields': ('salary_min', 'salary_max')
        }),
        ('Additional Information', {
            'fields': ('experience_level', 'requirements', 'benefits')
        }),
        ('Dates & Status', {
            'fields': ('expiry_date', 'is_active', 'created_at', 'updated_at')
        }),
    )
