from django.http import HttpResponse

def login(request):
    return HttpResponse("Please log in!")

def profile(request):
    return HttpResponse("Here is your profile.")