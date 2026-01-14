from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import RecruiterProfile

# Create your views here.

@login_required
def post_job(request):
    profile = RecruiterProfile.objects.get(user=request.user)
    return render(request, "Dashboard/post_job.html", {
        "profile": profile
    })
