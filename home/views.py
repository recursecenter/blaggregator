from django.http import HttpResponse

from home.models import User

def login(request):
    return HttpResponse("Please log in!")

def profile(request, user_id):
    return HttpResponse("Here is the profile for user number %s." % user_id)