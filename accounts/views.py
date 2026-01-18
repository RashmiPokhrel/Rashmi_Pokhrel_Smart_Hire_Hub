from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from .models import User, RecruiterProfile,JobSeekerProfile
import json
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

#Forget password
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .models import User, PasswordResetOTP




def home(request):
    from jobs.models import Job
    from django.utils import timezone
    from datetime import timedelta
    
    # Mark expired jobs as inactive
    Job.mark_all_expired_inactive()
    
    # Get latest 3 active jobs
    latest_jobs = Job.get_active_jobs().select_related('recruiter', 'recruiter__user').order_by('-created_at')[:3]
    
    # Calculate time ago for each job
    jobs_with_time = []
    for job in latest_jobs:
        time_diff = timezone.now() - job.created_at
        if time_diff < timedelta(minutes=1):
            time_ago = "Just now"
        elif time_diff < timedelta(hours=1):
            minutes = int(time_diff.total_seconds() / 60)
            time_ago = f"{minutes} min ago"
        elif time_diff < timedelta(days=1):
            hours = int(time_diff.total_seconds() / 3600)
            time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif time_diff < timedelta(days=7):
            days = int(time_diff.total_seconds() / 86400)
            time_ago = f"{days} day{'s' if days > 1 else ''} ago"
        else:
            time_ago = job.created_at.strftime("%b %d, %Y")
        
        jobs_with_time.append({
            'job': job,
            'time_ago': time_ago
        })
    
    return render(request, 'hire/home.html', {
        'latest_jobs': jobs_with_time
    })

@csrf_exempt



def register_user(request):
    if request.method == 'GET':
        return render(request, 'hire/register.html')
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            role = data.get('role')
            password = data.get('password')
            confirm_password = data.get('confirm_password')

            # 🔹 COMMON PASSWORD CHECK
            if not password or not confirm_password:
                return JsonResponse({'error': 'Password fields are required'}, status=400)

            if password != confirm_password:
                return JsonResponse({'error': 'Passwords do not match'}, status=400)

            if len(password) < 6:
                return JsonResponse({'error': 'Password must be at least 6 characters long'}, status=400)

          
            # JOB SEEKER REGISTRATION
         
            if role == 'job_seeker':
                username = data.get('username')
                email = data.get('email')

                if not username or not email:
                    return JsonResponse({'error': 'Username and email are required'}, status=400)

                if User.objects.filter(username=username).exists():
                    return JsonResponse({'error': 'Username already exists'}, status=400)

                if User.objects.filter(email=email).exists():
                    return JsonResponse({'error': 'Email already registered'}, status=400)

                user = User.objects.create(
                    username=username,
                    email=email,
                    role='job_seeker',
                    password=make_password(password)
                )

            # RECRUITER REGISTRATION
          
            elif role == 'recruiter':
                company_name = data.get('company_name')
                company_email = data.get('company_email')
                company_phone = data.get('company_phone')

                if not company_name or not company_email or not company_phone:
                    return JsonResponse(
                        {'error': 'Company name, email, and phone are required'},
                        status=400
                    )

                # company name acts as username
                if User.objects.filter(username=company_name).exists():
                    return JsonResponse(
                        {'error': 'Company already registered'},
                        status=400
                    )

                if User.objects.filter(email=company_email).exists():
                    return JsonResponse(
                        {'error': 'Company email already registered'},
                        status=400
                    )

                user = User.objects.create(
                    username=company_name,
                    email=company_email,
                    role='recruiter',
                    password=make_password(password)
                )

                RecruiterProfile.objects.create(
                    user=user,
                    company_name=company_name,
                    company_email=company_email,
                    company_phone=company_phone,
                    company_address=data.get('company_address')
                )

            else:
                return JsonResponse({'error': 'Invalid role'}, status=400)

            return JsonResponse({'message': 'Registration successful'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

        except IntegrityError:
            return JsonResponse({'error': 'User already exists'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def login_user(request):

    #  Render login page
    if request.method == 'GET':
        return render(request, 'hire/login.html')

    #  Handle login request
    if request.method == "POST":

        # Safely parse JSON
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON data"},
                status=400
            )

        username = data.get("username")
        password = data.get("password")

        # Validate inputs
        if not username or not password:
            return JsonResponse(
                {"error": "Username and password required"},
                status=400
            )

        # Authenticate user
        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            # RETURN ROLE FOR DASHBOARD REDIRECTION
            return JsonResponse({
                "success": True,
                "role": user.role
            }, status=200)

        else:
            return JsonResponse(
                {"error": "Invalid username or password"},
                status=401
            )

    return JsonResponse(
        {"error": "Invalid request method"},
        status=405
    )





@csrf_exempt
def send_reset_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')

            if not email:
                return JsonResponse({'error': 'Email is required'}, status=400)

            if not User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Email not registered'}, status=404)

            # Generate 6-digit OTP
            otp = get_random_string(length=6, allowed_chars='0123456789')

            # Save OTP
            PasswordResetOTP.objects.create(
                email=email,
                otp=otp
            )

            # Send Email
            send_mail(
                subject='Smart Hire Hub - Password Reset OTP',
                message=f'Your OTP is {otp}. It is valid for 10 minutes.',
                from_email=None,
                recipient_list=[email],
            )

            return JsonResponse({'message': 'OTP sent to email'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def verify_reset_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            otp = data.get('otp')

            record = PasswordResetOTP.objects.filter(
                email=email,
                otp=otp
            ).last()

            if not record:
                return JsonResponse({'error': 'Invalid OTP'}, status=400)

            if record.is_expired():
                return JsonResponse({'error': 'OTP expired'}, status=400)

            return JsonResponse({'message': 'OTP verified'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def password_reset_view(request):
    if request.method == 'GET':
        return render(request, 'hire/reset.html')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            new_password = data.get('password')
            confirm_password = data.get('confirm_password')

            if new_password != confirm_password:
                return JsonResponse({'error': 'Passwords do not match'}, status=400)

            user = User.objects.get(email=email)
            user.password = make_password(new_password)
            user.save()

            # Delete used OTPs
            PasswordResetOTP.objects.filter(email=email).delete()

            return JsonResponse({'message': 'Password reset successful'}, status=200)

        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def edit_profile(request):
    profile, created = JobSeekerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name")
        profile.phone = request.POST.get("phone")
        profile.location = request.POST.get("location")
        profile.bio = request.POST.get("bio")

        if "profile_image" in request.FILES:
            profile.profile_image = request.FILES["profile_image"]

        profile.save()

        # REDIRECT after save (IMPORTANT)
        return redirect("jobseeker_dashboard")

    return render(request, "hire/edit_job_seeker.html", {
        "profile": profile
    })


@csrf_exempt   
@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        
        return redirect('login') 
    



@login_required
def jobseeker_dashboard(request):
    from jobs.models import Job, Application
    
    # Get job seeker profile if exists
    try:
        profile = JobSeekerProfile.objects.get(user=request.user)
    except JobSeekerProfile.DoesNotExist:
        profile = None
    
    # Calculate statistics
    # Count applications by this job seeker
    try:
        applications_count = Application.objects.filter(candidate=profile).count() if profile else 0
    except:
        applications_count = 0
    
    # Calculate profile completion (placeholder for now)
    profile_completion = 30  # TODO: Calculate based on filled fields
    
    return render(request, "Dashboard/Jobseeker.html", {
        "profile": profile,
        "applications_count": applications_count,
        "profile_completion": profile_completion
    })


@login_required
def browse_jobs(request):
    """
    Browse all available jobs - separate page for job listings
    """
    from jobs.models import Job
    
    if request.user.role != 'job_seeker':
        messages.error(request, 'Only job seekers can browse jobs.')
        return redirect('jobseeker_dashboard')
    
    # Get all active jobs (not expired and is_active=True)
    # Automatically mark expired jobs as inactive
    Job.mark_all_expired_inactive()
    
    # Fetch all active jobs with filters
    jobs = Job.get_active_jobs().select_related('recruiter', 'recruiter__user').order_by('-created_at')
    
    # Get filter parameters
    location_filter = request.GET.get('location', '')
    job_type_filter = request.GET.get('job_type', '')
    experience_filter = request.GET.get('experience', '')
    search_query = request.GET.get('search', '')
    
    # Apply filters
    if location_filter:
        jobs = jobs.filter(location__icontains=location_filter)
    
    if job_type_filter:
        jobs = jobs.filter(job_type=job_type_filter)
    
    if experience_filter:
        jobs = jobs.filter(experience_level=experience_filter)
    
    if search_query:
        jobs = jobs.filter(
            Q(job_title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(recruiter__company_name__icontains=search_query)
        )
    
    # Get job seeker profile
    try:
        profile = JobSeekerProfile.objects.get(user=request.user)
    except JobSeekerProfile.DoesNotExist:
        profile = None
    
    return render(request, "Dashboard/browse_jobs.html", {
        "jobs": jobs,
        "profile": profile,
        "location_filter": location_filter,
        "job_type_filter": job_type_filter,
        "experience_filter": experience_filter,
        "search_query": search_query
    })

@login_required
def recruiter_dashboard(request):
    from jobs.models import Job
    
    profile = RecruiterProfile.objects.get(user=request.user)
    
    # Automatically mark expired jobs as inactive
    Job.mark_all_expired_inactive()
    
    # Calculate real job statistics
    total_jobs = Job.objects.filter(recruiter=profile).count()
    active_jobs = Job.get_active_jobs(recruiter=profile).count()
    # TODO: Calculate total applications when application model is created
    total_applications = 0  # Placeholder for now
    
    return render(request, "Dashboard/recuriter.html", {
        "profile": profile,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_applications": total_applications
    })

from django.contrib.auth import update_session_auth_hash

@login_required
def account_settings(request):
    user = request.user

    if request.method == "POST":

        # CHANGE PASSWORD
        if 'change_password' in request.POST:
            current = request.POST.get('current_password')
            new = request.POST.get('new_password')
            confirm = request.POST.get('confirm_password')

            if not user.check_password(current):
                messages.error(request, "Current password is incorrect")
            elif new != confirm:
                messages.error(request, "Passwords do not match")
            else:
                user.set_password(new)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password updated successfully")

        # CHANGE EMAIL
        elif 'change_email' in request.POST:
            user.email = request.POST.get('new_email')
            user.save()
            messages.success(request, "Email updated successfully")

        # PERSONAL INFORMATION
        elif 'personal_info' in request.POST:
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.save()
            messages.success(request, "Personal information updated")

        return redirect('account_settings')

    return render(request, "settings/account_settings.html")


@login_required
def edit_recruiter_profile(request):
    profile = RecruiterProfile.objects.get(user=request.user)

    if request.method == "POST":
        profile.company_name = request.POST.get("company_name")
        profile.company_email = request.POST.get("company_email")
        profile.company_phone = request.POST.get("company_phone")
        profile.company_address = request.POST.get("company_address")

        if request.FILES.get("profile_image"):
            profile.profile_image = request.FILES.get("profile_image")

        profile.save()
        return redirect("recruiter_dashboard")

    return render(request, "hire/edit_recuriter.html", {
        "profile": profile
    })


# Recruiter Account Settings

@login_required
def recruiter_account_settings(request):
    if request.method == "POST":
        if request.POST.get("new_password"):
            request.user.set_password(request.POST.get("new_password"))
            request.user.save()
            update_session_auth_hash(request, request.user)
            return redirect('recruiter_account_settings')

    return render(request, 'settings/recuriter_account_setting.html')