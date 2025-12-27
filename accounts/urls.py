from django.urls import path
from .views import register_user,login_user,logout_view,home, password_reset_view

urlpatterns = [
    path("home/", home, name="home"),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path("reset/", password_reset_view, name="password_reset"),
    path('logout/', logout_view, name='logout')

]
