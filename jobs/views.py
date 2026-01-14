from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
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


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def save_job(request):
    """
    API endpoint to save a job posted by the logged-in recruiter.
    Validates recruiter ownership and saves the job.
    """
    try:
        # Validate user is a recruiter
        if request.user.role != 'recruiter':
            return JsonResponse({
                'success': False,
                'error': 'Only recruiters can post jobs.'
            }, status=403)
        
        # Get recruiter profile
        try:
            recruiter_profile = RecruiterProfile.objects.get(user=request.user)
        except RecruiterProfile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Recruiter profile not found. Please complete your profile.'
            }, status=404)
        
        # Parse JSON data
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data.'
            }, status=400)
        
        # Validate required fields
        required_fields = ['job_title', 'description', 'location', 'job_type', 'expiry_date']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return JsonResponse({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=400)
        
        # Validate expiry date
        try:
            expiry_date = datetime.strptime(data.get('expiry_date'), '%Y-%m-%d').date()
            if expiry_date < timezone.now().date():
                return JsonResponse({
                    'success': False,
                    'error': 'Expiry date cannot be in the past.'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD.'
            }, status=400)
        
        # Validate job type
        valid_job_types = [choice[0] for choice in Job.JOB_TYPE_CHOICES]
        if data.get('job_type') not in valid_job_types:
            return JsonResponse({
                'success': False,
                'error': f'Invalid job type. Must be one of: {", ".join(valid_job_types)}'
            }, status=400)
        
        # Validate salary range if provided
        salary_min = None
        salary_max = None
        
        if data.get('salary_min'):
            try:
                salary_min = float(data.get('salary_min'))
                if salary_min < 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'Minimum salary cannot be negative.'
                    }, status=400)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid minimum salary value.'
                }, status=400)
        
        if data.get('salary_max'):
            try:
                salary_max = float(data.get('salary_max'))
                if salary_max < 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'Maximum salary cannot be negative.'
                    }, status=400)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid maximum salary value.'
                }, status=400)
        
        # Validate salary range logic
        if salary_min and salary_max and salary_min > salary_max:
            return JsonResponse({
                'success': False,
                'error': 'Minimum salary cannot be greater than maximum salary.'
            }, status=400)
        
        # Validate experience level if provided
        experience_level = data.get('experience_level')
        if experience_level:
            valid_experience_levels = [choice[0] for choice in Job.EXPERIENCE_LEVEL_CHOICES]
            if experience_level not in valid_experience_levels:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid experience level. Must be one of: {", ".join(valid_experience_levels)}'
                }, status=400)
        
        # Create job instance
        job = Job.objects.create(
            recruiter=recruiter_profile,  # Validate recruiter ownership here
            job_title=data.get('job_title').strip(),
            description=data.get('description').strip(),
            location=data.get('location').strip(),
            job_type=data.get('job_type'),
            salary_min=salary_min,
            salary_max=salary_max,
            experience_level=experience_level if experience_level else None,
            requirements=data.get('requirements', '').strip() or None,
            benefits=data.get('benefits', '').strip() or None,
            expiry_date=expiry_date,
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Job posted successfully!',
            'job': {
                'id': job.id,
                'job_title': job.job_title,
                'location': job.location,
                'job_type': job.get_job_type_display(),
                'expiry_date': job.expiry_date.strftime('%Y-%m-%d'),
                'created_at': job.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }, status=201)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)
