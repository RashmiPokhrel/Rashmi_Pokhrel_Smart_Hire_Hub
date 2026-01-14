from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from datetime import datetime
import json
from accounts.models import RecruiterProfile
from .models import Job

# Create your views here.

@login_required
def post_job(request):
    profile = RecruiterProfile.objects.get(user=request.user)
    return render(request, "Dashboard/post_job.html", {
        "profile": profile
    })


@login_required
def my_jobs(request):
    """
    Display all jobs posted by the logged-in recruiter.
    """
    if request.user.role != 'recruiter':
        messages.error(request, 'Only recruiters can access this page.')
        return redirect('recruiter_dashboard')
    
    try:
        recruiter_profile = RecruiterProfile.objects.get(user=request.user)
        jobs = Job.objects.filter(recruiter=recruiter_profile).order_by('-created_at')
        
        return render(request, "Dashboard/my_jobs.html", {
            "profile": recruiter_profile,
            "jobs": jobs
        })
    except RecruiterProfile.DoesNotExist:
        messages.error(request, 'Recruiter profile not found. Please complete your profile.')
        return redirect('recruiter_dashboard')


@login_required
def save_job(request):
    """
    Save a job posted by the logged-in recruiter.
    Handles both form submissions and API calls.
    On success, redirects to My Jobs page.
    """
    if request.method != 'POST':
        return redirect('post_job')
    
    try:
        # Validate user is a recruiter
        if request.user.role != 'recruiter':
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'Only recruiters can post jobs.'
                }, status=403)
            messages.error(request, 'Only recruiters can post jobs.')
            return redirect('post_job')
        
        # Get recruiter profile
        try:
            recruiter_profile = RecruiterProfile.objects.get(user=request.user)
        except RecruiterProfile.DoesNotExist:
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'Recruiter profile not found. Please complete your profile.'
                }, status=404)
            messages.error(request, 'Recruiter profile not found. Please complete your profile.')
            return redirect('post_job')
        
        # Parse data (handle both JSON and form data)
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON data.'
                }, status=400)
        else:
            data = request.POST
        
        # Validate required fields
        required_fields = ['job_title', 'description', 'location', 'job_type', 'expiry_date']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            error_msg = f'Missing required fields: {", ".join(missing_fields)}'
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=400)
            messages.error(request, error_msg)
            return redirect('post_job')
        
        # Validate expiry date
        try:
            expiry_date = datetime.strptime(data.get('expiry_date'), '%Y-%m-%d').date()
            if expiry_date < timezone.now().date():
                error_msg = 'Expiry date cannot be in the past.'
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    }, status=400)
                messages.error(request, error_msg)
                return redirect('post_job')
        except ValueError:
            error_msg = 'Invalid date format. Use YYYY-MM-DD.'
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=400)
            messages.error(request, error_msg)
            return redirect('post_job')
        
        # Validate job type
        valid_job_types = [choice[0] for choice in Job.JOB_TYPE_CHOICES]
        if data.get('job_type') not in valid_job_types:
            error_msg = f'Invalid job type. Must be one of: {", ".join(valid_job_types)}'
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=400)
            messages.error(request, error_msg)
            return redirect('post_job')
        
        # Validate salary range if provided
        salary_min = None
        salary_max = None
        
        if data.get('salary_min'):
            try:
                salary_min = float(data.get('salary_min'))
                if salary_min < 0:
                    error_msg = 'Minimum salary cannot be negative.'
                    if request.content_type == 'application/json':
                        return JsonResponse({'success': False, 'error': error_msg}, status=400)
                    messages.error(request, error_msg)
                    return redirect('post_job')
            except ValueError:
                error_msg = 'Invalid minimum salary value.'
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('post_job')
        
        if data.get('salary_max'):
            try:
                salary_max = float(data.get('salary_max'))
                if salary_max < 0:
                    error_msg = 'Maximum salary cannot be negative.'
                    if request.content_type == 'application/json':
                        return JsonResponse({'success': False, 'error': error_msg}, status=400)
                    messages.error(request, error_msg)
                    return redirect('post_job')
            except ValueError:
                error_msg = 'Invalid maximum salary value.'
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('post_job')
        
        # Validate salary range logic
        if salary_min and salary_max and salary_min > salary_max:
            error_msg = 'Minimum salary cannot be greater than maximum salary.'
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect('post_job')
        
        # Validate experience level if provided
        experience_level = data.get('experience_level')
        if experience_level:
            valid_experience_levels = [choice[0] for choice in Job.EXPERIENCE_LEVEL_CHOICES]
            if experience_level not in valid_experience_levels:
                error_msg = f'Invalid experience level. Must be one of: {", ".join(valid_experience_levels)}'
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('post_job')
        
        # Create job instance
        requirements = data.get('requirements', '').strip() if data.get('requirements') else None
        benefits = data.get('benefits', '').strip() if data.get('benefits') else None
        
        job = Job.objects.create(
            recruiter=recruiter_profile,  # Validate recruiter ownership here
            job_title=data.get('job_title').strip(),
            description=data.get('description').strip(),
            location=data.get('location').strip(),
            job_type=data.get('job_type'),
            salary_min=salary_min,
            salary_max=salary_max,
            experience_level=experience_level if experience_level else None,
            requirements=requirements,
            benefits=benefits,
            expiry_date=expiry_date,
            is_active=True
        )
        
        # Handle response based on request type
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Job posted successfully!',
                'redirect_url': '/my-jobs/',
                'job': {
                    'id': job.id,
                    'job_title': job.job_title,
                    'location': job.location,
                    'job_type': job.get_job_type_display(),
                    'expiry_date': job.expiry_date.strftime('%Y-%m-%d'),
                    'created_at': job.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }, status=201)
        else:
            # Form submission - redirect to My Jobs
            messages.success(request, 'Job posted successfully!')
            return redirect('my_jobs')
        
    except Exception as e:
        error_msg = f'An error occurred: {str(e)}'
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)
        messages.error(request, error_msg)
        return redirect('post_job')
