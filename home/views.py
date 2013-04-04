from django.http import HttpResponse
from django.template import Context, loader, RequestContext
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
import requests

from home.models import User

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        resp = requests.get('https://www.hackerschool.com/auth', params={'email':email, 'password':password})
        if resp.status_code == requests.codes.ok:
            return HttpResponse("Success!")
        else:
            return HttpResponse("Auth Failed! Error code %s" % resp.status_code)
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