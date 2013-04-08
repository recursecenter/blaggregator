from django.http import HttpResponse
from django.template import Context, loader, RequestContext
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from home.models import User
import requests

from home.models import User

def login(request):
    ''''''
    if request.method == 'POST':

        email = request.POST['email']
        password = request.POST['password']

        resp = requests.get('https://www.hackerschool.com/auth', params={'email':email, 'password':password})

        if resp.status_code == requests.codes.ok:
            r = resp.json()
            try:
                user = User.objects.get(hs_id = r['hs_id'])
                #return HttpResponse("Welcome back %s! Returning user %s" % (r['first_name'], r['hs_id']))
            except:
                # create a new account
                user = User(email = email,
                            hs_id = r['hs_id'],
                            first_name = r['first_name'],
                            last_name = r['last_name'],
                            github = r['github'],
                            twitter = r['twitter'],
                            irc = r['irc']
                            )
                user.save()
                #return HttpResponse("Just created user %s with id %s" % (r['first_name'], r['hs_id']))
            return render_to_response('home/new.html')
        else:
            return HttpResponse("Auth Failed! Error code %s" % resp.status_code)
    else:
        # todo: serve error!
        return render_to_response('home/login.html', {},
                                   context_instance=RequestContext(request))

def profile(request, user_id):
    current_user = User.objects.get(hs_id=user_id)
    template = loader.get_template('home/index.html')
    context = Context({
        'current_user': current_user,
    })
    return HttpResponse(template.render(context))

def new(request):
    return render_to_response('home/new.html')
