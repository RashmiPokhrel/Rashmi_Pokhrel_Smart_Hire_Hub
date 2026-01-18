from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from datetime import datetime
import json
from accounts.models import RecruiterProfile
from .models import Job, Application

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
    Automatically marks expired jobs as inactive.
    """
    if request.user.role != 'recruiter':
        messages.error(request, 'Only recruiters can access this page.')
        return redirect('recruiter_dashboard')
    
    try:
        recruiter_profile = RecruiterProfile.objects.get(user=request.user)
        
        # Automatically mark expired jobs as inactive
        Job.mark_all_expired_inactive()
        
        # Get all jobs for this recruiter (including inactive/expired ones)
        jobs = Job.objects.filter(recruiter=recruiter_profile).order_by('-created_at')
        
        return render(request, "Dashboard/my_jobs.html", {
            "profile": recruiter_profile,
            "jobs": jobs
        })
    except RecruiterProfile.DoesNotExist:
        messages.error(request, 'Recruiter profile not found. Please complete your profile.')
        return redirect('recruiter_dashboard')


@login_required
def edit_job(request, job_id):
    """
    Edit a job posted by the logged-in recruiter.
    Handles both GET (display form) and POST (update job).
    Validates recruiter ownership.
    """
    if request.user.role != 'recruiter':
        messages.error(request, 'Only recruiters can edit jobs.')
        return redirect('recruiter_dashboard')
    
    try:
        recruiter_profile = RecruiterProfile.objects.get(user=request.user)
        job = Job.objects.get(id=job_id, recruiter=recruiter_profile)
    except Job.DoesNotExist:
        messages.error(request, 'Job not found or you do not have permission to edit this job.')
        return redirect('my_jobs')
    except RecruiterProfile.DoesNotExist:
        messages.error(request, 'Recruiter profile not found.')
        return redirect('recruiter_dashboard')
    
    # Handle GET request - display edit form
    if request.method == 'GET':
        return render(request, "Dashboard/edit_job.html", {
            "profile": recruiter_profile,
            "job": job
        })
    
    # Handle POST request - update job
    if request.method == 'POST':
        try:
            data = request.POST
            
            # Validate required fields
            required_fields = ['job_title', 'description', 'location', 'job_type', 'expiry_date']
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                error_msg = f'Missing required fields: {", ".join(missing_fields)}'
                messages.error(request, error_msg)
                return render(request, "Dashboard/edit_job.html", {
                    "profile": recruiter_profile,
                    "job": job
                })
            
            # Validate expiry date
            try:
                expiry_date = datetime.strptime(data.get('expiry_date'), '%Y-%m-%d').date()
                if expiry_date < timezone.now().date():
                    error_msg = 'Expiry date cannot be in the past.'
                    messages.error(request, error_msg)
                    return render(request, "Dashboard/edit_job.html", {
                        "profile": recruiter_profile,
                        "job": job
                    })
            except ValueError:
                error_msg = 'Invalid date format. Use YYYY-MM-DD.'
                messages.error(request, error_msg)
                return render(request, "Dashboard/edit_job.html", {
                    "profile": recruiter_profile,
                    "job": job
                })
            
            # Validate job type
            valid_job_types = [choice[0] for choice in Job.JOB_TYPE_CHOICES]
            if data.get('job_type') not in valid_job_types:
                error_msg = f'Invalid job type. Must be one of: {", ".join(valid_job_types)}'
                messages.error(request, error_msg)
                return render(request, "Dashboard/edit_job.html", {
                    "profile": recruiter_profile,
                    "job": job
                })
            
            # Validate salary range if provided
            salary_min = None
            salary_max = None
            
            if data.get('salary_min'):
                try:
                    salary_min = float(data.get('salary_min'))
                    if salary_min < 0:
                        error_msg = 'Minimum salary cannot be negative.'
                        messages.error(request, error_msg)
                        return render(request, "Dashboard/edit_job.html", {
                            "profile": recruiter_profile,
                            "job": job
                        })
                except ValueError:
                    error_msg = 'Invalid minimum salary value.'
                    messages.error(request, error_msg)
                    return render(request, "Dashboard/edit_job.html", {
                        "profile": recruiter_profile,
                        "job": job
                    })
            
            if data.get('salary_max'):
                try:
                    salary_max = float(data.get('salary_max'))
                    if salary_max < 0:
                        error_msg = 'Maximum salary cannot be negative.'
                        messages.error(request, error_msg)
                        return render(request, "Dashboard/edit_job.html", {
                            "profile": recruiter_profile,
                            "job": job
                        })
                except ValueError:
                    error_msg = 'Invalid maximum salary value.'
                    messages.error(request, error_msg)
                    return render(request, "Dashboard/edit_job.html", {
                        "profile": recruiter_profile,
                        "job": job
                    })
            
            # Validate salary range logic
            if salary_min and salary_max and salary_min > salary_max:
                error_msg = 'Minimum salary cannot be greater than maximum salary.'
                messages.error(request, error_msg)
                return render(request, "Dashboard/edit_job.html", {
                    "profile": recruiter_profile,
                    "job": job
                })
            
            # Validate experience level if provided
            experience_level = data.get('experience_level')
            if experience_level:
                valid_experience_levels = [choice[0] for choice in Job.EXPERIENCE_LEVEL_CHOICES]
                if experience_level not in valid_experience_levels:
                    error_msg = f'Invalid experience level. Must be one of: {", ".join(valid_experience_levels)}'
                    messages.error(request, error_msg)
                    return render(request, "Dashboard/edit_job.html", {
                        "profile": recruiter_profile,
                        "job": job
                    })
            
            # Handle requirements and benefits (store None for empty strings)
            requirements = data.get('requirements', '').strip() if data.get('requirements') else None
            benefits = data.get('benefits', '').strip() if data.get('benefits') else None
            
            # Handle is_active checkbox (checkbox sends 'on' if checked, nothing if unchecked)
            is_active = data.get('is_active') == 'on'
            
            # Update job instance
            job.job_title = data.get('job_title').strip()
            job.description = data.get('description').strip()
            job.location = data.get('location').strip()
            job.job_type = data.get('job_type')
            job.salary_min = salary_min
            job.salary_max = salary_max
            job.experience_level = experience_level if experience_level else None
            job.requirements = requirements
            job.benefits = benefits
            job.expiry_date = expiry_date
            job.is_active = is_active
            job.save()  # This will also update the updated_at field automatically
            
            messages.success(request, f'Job "{job.job_title}" has been updated successfully!')
            return redirect('my_jobs')
            
        except Exception as e:
            error_msg = f'An error occurred while updating the job: {str(e)}'
            messages.error(request, error_msg)
            return render(request, "Dashboard/edit_job.html", {
                "profile": recruiter_profile,
                "job": job
            })


@login_required
def view_applications(request, job_id):
    """
    View applications for a specific job.
    Validates recruiter ownership.
    """
    if request.user.role != 'recruiter':
        messages.error(request, 'Only recruiters can view applications.')
        return redirect('recruiter_dashboard')
    
    try:
        recruiter_profile = RecruiterProfile.objects.get(user=request.user)
        job = Job.objects.get(id=job_id, recruiter=recruiter_profile)
        
        # TODO: Implement applications view
        messages.info(request, f'Applications for "{job.job_title}" - Coming soon.')
        return redirect('my_jobs')
        
    except Job.DoesNotExist:
        messages.error(request, 'Job not found or you do not have permission to view applications for this job.')
        return redirect('my_jobs')
    except RecruiterProfile.DoesNotExist:
        messages.error(request, 'Recruiter profile not found.')
        return redirect('recruiter_dashboard')


@login_required
def delete_job(request, job_id):
    """
    Delete a job posted by the logged-in recruiter.
    Validates recruiter ownership.
    """
    if request.method != 'POST':
        return redirect('my_jobs')
    
    if request.user.role != 'recruiter':
        messages.error(request, 'Only recruiters can delete jobs.')
        return redirect('my_jobs')
    
    try:
        recruiter_profile = RecruiterProfile.objects.get(user=request.user)
        job = Job.objects.get(id=job_id, recruiter=recruiter_profile)
        job_title = job.job_title
        job.delete()
        messages.success(request, f'Job "{job_title}" has been deleted successfully.')
    except Job.DoesNotExist:
        messages.error(request, 'Job not found or you do not have permission to delete this job.')
    except RecruiterProfile.DoesNotExist:
        messages.error(request, 'Recruiter profile not found.')
    except Exception as e:
        messages.error(request, f'An error occurred while deleting the job: {str(e)}')
    
    return redirect('my_jobs')


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


@login_required
def applications(request):
    """
    Display all applications for jobs posted by the logged-in recruiter.
    """
    if request.user.role != 'recruiter':
        messages.error(request, 'Only recruiters can access this page.')
        return redirect('recruiter_dashboard')
    
    try:
        recruiter_profile = RecruiterProfile.objects.get(user=request.user)
        
        # Get all applications for jobs posted by this recruiter
        applications = Application.objects.filter(
            job__recruiter=recruiter_profile
        ).select_related('job', 'candidate', 'candidate__user').order_by('-applied_date')
        
        # Get filter parameters
        job_filter = request.GET.get('job', '')
        status_filter = request.GET.get('status', '')
        
        # Apply filters
        if job_filter:
            applications = applications.filter(job_id=job_filter)
        
        if status_filter:
            applications = applications.filter(status=status_filter)
        
        # Get all jobs for filter dropdown
        jobs = Job.objects.filter(recruiter=recruiter_profile).order_by('-created_at')
        
        # Count applications by status
        total_applications = applications.count()
        pending_count = Application.objects.filter(
            job__recruiter=recruiter_profile,
            status='pending'
        ).count()
        shortlisted_count = Application.objects.filter(
            job__recruiter=recruiter_profile,
            status='shortlisted'
        ).count()
        
        return render(request, "Dashboard/applications.html", {
            "profile": recruiter_profile,
            "applications": applications,
            "jobs": jobs,
            "selected_job": job_filter,
            "selected_status": status_filter,
            "total_applications": total_applications,
            "pending_count": pending_count,
            "shortlisted_count": shortlisted_count,
        })
    except RecruiterProfile.DoesNotExist:
        messages.error(request, 'Recruiter profile not found. Please complete your profile.')
        return redirect('recruiter_dashboard')


@login_required
def update_application_status(request, application_id):
    """
    Update the status of an application (Shortlisted or Rejected).
    Only accessible by the recruiter who owns the job.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
    
    if request.user.role != 'recruiter':
        return JsonResponse({'success': False, 'error': 'Only recruiters can update application status.'}, status=403)
    
    try:
        recruiter_profile = RecruiterProfile.objects.get(user=request.user)
        application = Application.objects.get(
            id=application_id,
            job__recruiter=recruiter_profile
        )
        
        # Get new status from request
        new_status = request.POST.get('status')
        
        # Parse JSON if content type is application/json
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                new_status = data.get('status')
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON data.'}, status=400)
        
        # Validate status
        valid_statuses = ['pending', 'reviewed', 'shortlisted', 'rejected', 'accepted']
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }, status=400)
        
        # Update status
        application.status = new_status
        application.save(update_fields=['status'])
        
        # Return success response
        return JsonResponse({
            'success': True,
            'message': f'Application status updated to {application.get_status_display()}.',
            'new_status': new_status,
            'new_status_display': application.get_status_display(),
            'new_status_class': application.get_status_display_class()
        })
        
    except Application.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Application not found or you do not have permission to update this application.'
        }, status=404)
    except RecruiterProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Recruiter profile not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)
