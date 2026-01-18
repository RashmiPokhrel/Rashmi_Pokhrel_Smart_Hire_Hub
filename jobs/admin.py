from django.contrib import admin
from .models import Job, Application


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


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'status', 'applied_date', 'updated_at')
    list_filter = ('status', 'applied_date', 'job__recruiter')
    search_fields = ('candidate__full_name', 'candidate__user__email', 'job__job_title', 'job__recruiter__company_name')
    readonly_fields = ('applied_date', 'updated_at')
    date_hierarchy = 'applied_date'
    
    fieldsets = (
        ('Application Details', {
            'fields': ('job', 'candidate', 'resume', 'cover_letter', 'status')
        }),
        ('Recruiter Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('applied_date', 'updated_at')
        }),
    )
