from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from .models import User, RecruiterProfile,JobSeekerProfile
import json
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.db import IntegrityError
from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

#Forget password
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .models import User, PasswordResetOTP




def home(request):
    return render(request, 'hire/home.html')

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

        #  REDIRECT after save (IMPORTANT)
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
    return render(request, "Dashboard/Jobseeker.html")

@login_required
def recruiter_dashboard(request):
    return render(request, "Dashboard/recruiter.html")


