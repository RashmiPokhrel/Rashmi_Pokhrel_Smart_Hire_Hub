from django.urls import path
from .views import post_job, save_job, my_jobs, edit_job, view_applications, delete_job, applications, update_application_status

urlpatterns = [
    path('post-job/', post_job, name='post_job'),
    path('api/save-job/', save_job, name='save_job'),
    path('my-jobs/', my_jobs, name='my_jobs'),
    path('edit-job/<int:job_id>/', edit_job, name='edit_job'),
    path('view-applications/<int:job_id>/', view_applications, name='view_applications'),
    path('delete-job/<int:job_id>/', delete_job, name='delete_job'),
    path('applications/', applications, name='applications'),
    path('api/update-application-status/<int:application_id>/', update_application_status, name='update_application_status'),
]
