from django.http import HttpResponse
from django.template import Context, loader, RequestContext
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
import requests

from home.models import User

def login(request):
    if request.method == 'POST':
        return HttpResponse(request.POST['email'])
        email = request.params.email
        password = request.params.password
        resp = requests.post('https://www.hackerschool.com/auth', auth=('email', 'password'))
        if resp.status_code == 200:
            return HttpResponse("Success!")
        else:
            return HttpResponse("Failed!")
    else:
        # todo: serve error!
        return render_to_response('home/login.html', {},
                                   context_instance=RequestContext(request))

def render_login_form():
    template = loader.get_template('home/login.html')
    return HttpResponse(template.render(RequestContext({})))

def profile(request, user_id):
    current_user = User.objects.get(hs_id=user_id)
    template = loader.get_template('home/index.html')
    context = Context({
        'current_user': current_user,
    })
    return HttpResponse(template.render(context))