from django.urls import path
from .views import post_job, save_job, my_jobs

urlpatterns = [
    path('post-job/', post_job, name='post_job'),
    path('api/save-job/', save_job, name='save_job'),
    path('my-jobs/', my_jobs, name='my_jobs'),
]
