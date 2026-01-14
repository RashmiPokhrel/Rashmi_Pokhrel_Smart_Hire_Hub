from django.urls import path
from .views import register_user,login_user,logout_view,home,password_reset_view,send_reset_otp,verify_reset_otp,edit_profile,jobseeker_dashboard,recruiter_dashboard,account_settings,recruiter_account_settings,edit_recruiter_profile

from django.shortcuts import render
from django.contrib.auth.decorators import login_required







urlpatterns = [
    path("home/", home, name="home"),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),

    path("reset/", password_reset_view, name="password_reset"),
    path('password/send-otp/', send_reset_otp),
    path('password/verify-otp/', verify_reset_otp),

    path('edit_profile/', edit_profile, name= 'edit_profile'),
    path('recruiter/edit-profile/', edit_recruiter_profile, name='edit_recruiter_profile'),
   
    


    path("jobseeker-dashboard/", jobseeker_dashboard, name="jobseeker_dashboard"),
    path("recruiter-dashboard/", recruiter_dashboard, name="recruiter_dashboard"),

    path('settings/', account_settings, name='account_settings'),
    path('recruiter/settings/', recruiter_account_settings, name='recruiter_account_settings'),

    path('logout/', logout_view, name='logout'),

]
