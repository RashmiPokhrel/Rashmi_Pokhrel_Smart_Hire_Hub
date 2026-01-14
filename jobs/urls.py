from django.urls import path
from .views import post_job

urlpatterns = [
    path('post-job/', post_job, name='post_job'),
]
