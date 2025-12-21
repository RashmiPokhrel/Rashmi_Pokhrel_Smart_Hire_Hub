from django.urls import path
from .views import register_user,login_user,logout_view

urlpatterns = [
    path('register/', register_user),
    path('login/', login_user),
    path('logout/', logout_view),

]
