from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from .models import User, RecruiterProfile
import json
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.db import IntegrityError
from django.shortcuts import render,redirect



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

            # =========================
            # JOB SEEKER REGISTRATION
            # =========================
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

            # =========================
            # RECRUITER REGISTRATION
            # =========================
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

    if request.method == 'GET':
        return render(request, 'hire/login.html')
    
    if request.method == "POST":

        # SAFELY PARSE JSON
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON data"},
                status=400
            )

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return JsonResponse(
                {"error": "Username and password required"},
                status=400
            )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return JsonResponse({"success": True})
        else:
            return JsonResponse(
                {"error": "Invalid username or password"},
                status=401
            )

    return JsonResponse({"error": "Invalid request method"}, status=405)


def password_reset_view(request):
    return render(request, "hire/reset.html")


@csrf_exempt
def logout_view(request):
    
 
    if request.method == "POST":
        logout(request)
        return redirect("login")  
    return redirect("login")


