from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from .models import User, RecruiterProfile
import json
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.db import IntegrityError



@csrf_exempt

def register_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            role = data.get('role')

            # Check required fields
            if not username or not email or not password or not role:
                return JsonResponse(
                    {'error': 'All fields are required'},
                    status=400
                )

            #  Password validation
            if len(password) < 6:
                return JsonResponse(
                    {'error': 'Password must be at least 6 characters long'},
                    status=400
                )

            #  Check username already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse(
                    {'error': 'Username already exists'},
                    status=400
                )

            # Check email already exists
            if User.objects.filter(email=email).exists():
                return JsonResponse(
                    {'error': 'Email already registered'},
                    status=400
                )

            #  Create user
            user = User.objects.create(
                username=username,
                email=email,
                role=role,
                password=make_password(password)
            )

            #  Recruiter profile creation
            if role == 'recruiter':
                company_name = data.get('company_name')
                company_email = data.get('company_email')

                if not company_name or not company_email:
                    return JsonResponse(
                        {'error': 'Company details are required for recruiter'},
                        status=400
                    )

                RecruiterProfile.objects.create(
                    user=user,
                    company_name=company_name,
                    company_email=company_email,
                    company_phone=data.get('company_phone'),
                    company_address=data.get('company_address')
                )

            return JsonResponse(
                {'message': 'Registration successful'},
                status=201
            )

        #  JSON error handling
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'Invalid JSON data'},
                status=400
            )

        # For No repitation of email
        except IntegrityError:
            return JsonResponse(
                {'error': 'User already exists'},
                status=400
            )

        # Any other unexpected error
        except Exception as e:
            return JsonResponse(
                {'error': str(e)},
                status=500
            )

    return JsonResponse(
        {'error': 'Invalid request method'},
        status=405
    )

@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse(
                {'error': 'Username and password are required'},
                status=400
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return JsonResponse(
                {'error': 'Invalid credentials'},
                status=401
            )

        login(request, user)

        return JsonResponse(
            {
                'message': 'Login successful',
                'username': user.username,
                'role': user.role
            },
            status=200
        )

    return JsonResponse({'error': 'Invalid request method'}, status=405)
@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        logout(request)

        return JsonResponse(
            {'message': 'Logout successful'},
            status=200
        )

    return JsonResponse({'error': 'Invalid request method'}, status=405)


