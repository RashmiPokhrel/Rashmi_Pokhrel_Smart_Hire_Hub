from django.urls import path
from .views import post_job, save_job

urlpatterns = [
    path('post-job/', post_job, name='post_job'),
    path('api/save-job/', save_job, name='save_job'),
]
