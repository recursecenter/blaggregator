from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template import Context, loader, RequestContext
from django.core.context_processors import csrf
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.shortcuts import render_to_response, render
from home.models import Hacker, Blog, Post, SubmittedPost
from django.conf import settings
from django.utils import timezone
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import connection
import random
import requests
import datetime
import re
import feedergrabber27

def log_in(request):
    ''' Log in a user who already has a pre-existing local account. '''

    if request.method == 'POST':

        email = request.POST['email']
        try:
            username = User.objects.get(email=email).username
        except:
            return HttpResponse("Bad login. Please check that you're using the correct credentials and try again.")
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            # if user exists locally:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/new')
            else:
                return HttpResponse("Your account is disabled. Please contact administrator for help.")

        else:
            return HttpResponse("Auth Failed! Please hit 'back' and try again.")
    else:
        return render_to_response('home/log_in.html', {},
                                   context_instance=RequestContext(request))

def create_account(request):
    ''' Create a new local user account. '''

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
    ''' Adds a blog to a user's profile as part of the create_account process. '''

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
            else:
                url = feed_url

            # create new blog record in db
            blog = Blog.objects.create(
                user=User.objects.get(id=request.user.id),
                feed_url=feed_url,
                url=url,
                created=datetime.datetime.now(),
            )
            blog.save()

            # Feedergrabber returns ( [(link, title, date)], [errors])
            # We're ignoring the errors returned for right now
            crawled, _ = feedergrabber27.feedergrabber(feed_url)

            for post in crawled:
                post_url, post_title, post_date = post
                newpost = Post.objects.create(
                  blog=Blog.objects.get(user=request.user.id),
                  url=post_url,
                  title=post_title,
                  content="",
                  date_updated=post_date,
                )

            return HttpResponseRedirect('/new')
        else:
            return HttpResponse("I didn't get your feed URL. Please go back and try again.")
    else:
        return HttpResponseRedirect('/new')

@login_required(login_url='/log_in')
def profile(request, user_id):
    ''' A user's profile. Not currently tied to a template - needs work. '''

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
    ''' Newest blog posts - main app view. '''


    new_posts = list(Post.objects.order_by('-date_updated')[:10])
    random_posts = list(Post.objects.raw("select distinct on(blog_id) blog_id, id, url, title, date_updated as date \
                                            from home_post order by blog_id, random()")[:5])

    for post in new_posts:
        user            = User.objects.get(blog__id__exact=post.blog_id)
        post.author     = user.first_name + " " + user.last_name
        post.authorid   = user.id
        post.avatar     = Hacker.objects.get(user=user.id).avatar_url

    for post in random_posts:
        user            = User.objects.get(blog__id__exact=post.blog_id)
        post.author     = user.first_name + " " + user.last_name
        post.authorid   = user.id
        post.avatar     = Hacker.objects.get(user=user.id).avatar_url

    context = Context({
        "new_posts": new_posts,
        "random_posts": random_posts,
    })

    return render_to_response('home/posts.html', context, context_instance=RequestContext(request))

@login_required(login_url='/log_in')
def feed(request):
    ''' Atom feed of all new posts. '''

    postList = list(Post.objects.all().order_by('-date_updated'))

    for post in postList:
        user = User.objects.get(blog__id__exact=post.blog_id)
        post.author = user.first_name + " " + user.last_name

    context = Context({
        "postList": postList,
        "domain": settings.SITE_URL
    })

    return render(request, 'home/atom.xml', context, content_type="text/xml")

@login_required(login_url='/log_in')
def submit_post(request):
    if request.method == 'POST': 
    	title = request.POST['title']
    	url = request.POST['url']
    	validate = URLValidator()

        try:
            validate(url)
            resp = requests.get(url)

            if resp.status_code == requests.codes.ok:
                date = timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone())
                SubmittedPost.objects.create(user=User.objects.get(id=request.user.id),url=url, title=title, date_submitted=date)
                return HttpResponseRedirect('/submitted_posts')
            else:
                context = Context({
                    "error_message": "URL does not exist. Please try again."
                })
        except ValidationError, e:
            context = Context({
                "error_message": "Invalid URL! Please enter a valid one."
            })
        
        return render_to_response('home/submit_post.html', context, context_instance=RequestContext(request))
    else:
		return render_to_response('home/submit_post.html', {}, context_instance=RequestContext(request))

@login_required(login_url='/log_in')
def submitted_posts(request):
    ''' Newest submitted posts - main app view. '''

    new_posts = list(SubmittedPost.objects.order_by('-date_submitted')[:10])
    random_posts = list(SubmittedPost.objects.raw("select distinct on(user_id) user_id, id, url, title, date_submitted as date \
                                                    from home_submittedpost order by user_id, random()"));

    for post in new_posts:
        user            = User.objects.get(id=post.user_id)
        post.author     = user.first_name + " " + user.last_name
        post.authorid   = user.id
        post.avatar     = Hacker.objects.get(user=user.id).avatar_url

    for post in random_posts:
        user            = User.objects.get(id=post.user_id)
        post.author     = user.first_name + " " + user.last_name
        post.authorid   = user.id
        post.avatar     = Hacker.objects.get(user=user.id).avatar_url

        context = Context({
            "new_posts": new_posts,
            "random_posts": random_posts
        })
    return render_to_response('home/posts.html', context, context_instance=RequestContext(request))


@login_required(login_url='/log_in')
def all_posts(request):
    ''' All posts - main app view. '''
    sql = "select blog_id as id, url, title, 'hacker_school' as type, date_updated as date from home_post union select user_id as id, url, title,\
          'submitted' as type, date_submitted as date from home_submittedpost order by date desc limit 10;"
    
    cursor = connection.cursor()
    cursor.execute(sql);
    new_posts = dictfetchall(cursor)

    #TODO: when there are less than 5 posts returned, what should the query be? or are we ok with just diplaying less than 5?
    sql = "(select distinct on(blog_id) blog_id as id, url, title, 'hacker_school' as type, date_updated as date from home_post order by blog_id, random() limit 10) \
            union (select distinct on(user_id) user_id as id, url, title, 'submitted' as type, date_submitted as date from home_submittedpost order by user_id, random() limit 10);"
    cursor.execute(sql);
    random_posts = dictfetchall(cursor)[0:5]

    for new_post in new_posts:
        if new_post['type'] == 'hacker_school':
            user = User.objects.get(blog__id__exact=new_post['id'])
        else:
            user = User.objects.get(id=new_post['id'])

        new_post['author']     = user.first_name + " " + user.last_name
        new_post['authorid']   = user.id
        new_post['avatar']     = Hacker.objects.get(user=user.id).avatar_url

    for random_post in random_posts:
        if random_post['type'] == 'hacker_school':
            user = User.objects.get(blog__id__exact=random_post['id'])
        else:
            user = User.objects.get(id=random_post['id'])

        random_post['author']     = user.first_name + " " + user.last_name
        random_post['authorid']   = user.id
        random_post['avatar']     = Hacker.objects.get(user=user.id).avatar_url

    context = Context({
    "new_posts" : new_posts,
    "random_posts" : random_posts
    })
    return render_to_response('home/posts.html', context, context_instance=RequestContext(request))


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]