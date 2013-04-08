from django.http import HttpResponse, Http404
from django.contrib.auth.models import User
from django.template import Context, loader, RequestContext
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
import requests

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
                return HttpResponse("Welcome back %s! Returning user %s" % (r['first_name'], r['hs_id']))
            except:
                # create a new account
                user = User.objects.create_user(r['first_name']+r['last_name'], email, password, id=r['hs_id'])
                user.hs_id = r['hs_id']
                user.first_name = r['first_name']
                user.last_name = r['last_name']
                user.github = r['github']
                user.twitter = r['twitter']
                user.irc = r['irc']

                user.save()
                uid = User.objects.get(username = "SashaLaundy")
                return HttpResponse("Just created user %s with id %s" % (r['first_name'], uid.id))
            return render_to_response('home/new.html')
        else:
            return HttpResponse("Auth Failed! Error code %s" % resp.status_code)
    else:
        # todo: serve error!
        return render_to_response('home/login.html', {},
                                   context_instance=RequestContext(request))

def profile(request, user_id):
    try:
        current_user = User.objects.get(hs_id=user_id)
        template = loader.get_template('home/index.html')
        context = Context({
            'current_user': current_user,
        })
    except User.DoesNotExist:
        raise Http404
    return HttpResponse(template.render(context))

def new(request):
    return render_to_response('home/new.html')
