from django.http import HttpResponse
from django.template import Context, loader

from home.models import User

def login(request):
    return HttpResponse("Please log in!")

def profile(request, user_id):
    current_user = User.objects.get(hs_id=user_id)
    template = loader.get_template('home/index.html')
    context = Context({
        'current_user': current_user,
    })
    return HttpResponse(template.render(context))