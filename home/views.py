from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template import Context, loader, RequestContext
from django.core.context_processors import csrf
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.shortcuts import render_to_response
from home.models import Hacker, Blog
import requests
import datetime
import re

def log_in(request):
    if request.method == 'POST':

        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(username=email, password=password)

        if user is not None:
            # if user exists locally:
            if user.is_active:
                login(request, user)
                #return HttpResponse("Welcome back, returning user %s!" % (email))
                return HttpResponseRedirect('/new')
            else:
                return HttpResponse("Your account is disabled. Please contact administrator for help.")

        else:
            return HttpResponse("Auth Failed! Please hit 'back' and try again.")
    else:
        return render_to_response('home/log_in.html', {},
                                   context_instance=RequestContext(request))

def create_account(request):
    if request.method == 'POST':

        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(email=email).count() > 0:
            return HttpResponse("You already have an account. Please <a href='/log_in'>log in</a> instead.")

        # auth against hacker school and create a new local account
        resp = requests.get('https://www.hackerschool.com/auth', params={'email':email, 'password':password})
        if resp.status_code == requests.codes.ok:
            r = resp.json()

            # construct new local account
            username = r['first_name']+r['last_name']
            user = User.objects.create_user(username, email, password, id=r['hs_id'])
            Hacker.objects.create(user=User.objects.get(id=r['hs_id']))
            user.first_name = r['first_name']
            user.last_name = r['last_name']
            user.hacker.github = r['github']
            user.hacker.twitter = r['twitter']
            user.hacker.irc = r['irc']
            user.hacker.avatar_url = r['image']
            user.save()
            user.hacker.save()

            # auth and log in locally
            current_user = authenticate(username=username, password=password)
            login(request, current_user)

            #return HttpResponse("Just created user %s with id %s" % (r['first_name'], r['hs_id']))
            template = loader.get_template('home/add_blog.html')
            context = RequestContext(request, {
                'current_user': current_user,
            })
            return HttpResponse(template.render(context))
        else:
            return HttpResponse("Auth Failed! (%s). Please hit 'back' and try again." % resp.status_code)
    return render_to_response('home/create_account.html', {}, context_instance=RequestContext(request))

@login_required(login_url='/log_in')
def add_blog(request):
    if request.method == 'POST':
        if request.POST['feed_url']:

            feed_url = request.POST['feed_url']

            # add http:// prefix if missing
            if feed_url[:4] != "http":
                feed_url = "http://" + feed_url

            # pull out human-readable url from feed_url
            # (naively - later we will crawl blog url for feed url)
            if re.search('atom.xml/*$', feed_url):
                url = re.sub('atom.xml/*$', '', feed_url)
            elif re.search('rss/*$', feed_url):
                url = re.sub('rss/*$', '', feed_url)

            # create new blog record in db
            blog = Blog.objects.create(
                                        user=User.objects.get(id=request.user.id),
                                        feed_url=feed_url,
                                        url=url,
                                        created=datetime.datetime.now(),
                                       )
            blog.save()
            return HttpResponseRedirect('/new')
        else:
            return HttpResponse("I didn't get your feed URL. Please go back and try again.")
    else:
        return HttpResponseRedirect('/new')

@login_required(login_url='/log_in')
def profile(request, user_id):
    try:
        current_user = User.objects.get(id=user_id)
        template = loader.get_template('home/index.html')
        context = Context({
            'current_user': current_user,
        })
    except User.DoesNotExist:
        raise Http404
    return HttpResponse(template.render(context))

@login_required(login_url='/log_in')
def new(request):

    blogList = list(Blog.objects.all()) # this is janky but temporary

    for blog in blogList:
        first_name  = User.objects.get(id=blog.user_id).first_name
        last_name   = User.objects.get(id=blog.user_id).last_name
        blog.author = first_name + " " + last_name
        blog.avatar  = Hacker.objects.get(user=blog.user_id).avatar_url

    context = Context({
        "blogList": blogList,
    })

    return render_to_response('home/new.html',
                              context,
                              context_instance=RequestContext(request))




