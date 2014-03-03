from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.template import Context, loader, RequestContext
from django.core.context_processors import csrf
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.shortcuts import render_to_response, render
from home.models import Hacker, Blog, Post, Comment
from django.conf import settings
import requests
import datetime
import re
import feedergrabber27
import random, string
import math
    
def get_post_info(slug):
    """ Gets the post object at a given slug. """
    post = Post.objects.get(slug=slug)
    user            = User.objects.get(blog__id__exact=post.blog_id)
    post.author     = user.first_name + " " + user.last_name
    post.authorid   = user.id
    post.avatar     = Hacker.objects.get(user=user.id).avatar_url
    post.slug       = slug
    return post
    
    
def get_comment_list(post):
    """ Gets the list of comment objects for a given post instance. """
    commentList = list(Comment.objects.filter(post=post).order_by('date_modified'))
    for comment in commentList:
        user            = User.objects.get(comment__slug__exact=comment.slug)
        comment.author  = user.first_name
        comment.avatar  = Hacker.objects.get(user=comment.user).avatar_url
        comment.authorid = comment.user.id
    return commentList


def framed(request, slug):
    ''' Display the article in an iframe with a navigation header back to blaggregator. '''

    post = get_post_info(slug)
    commentList = get_comment_list(post)
    post.commentcount = len(commentList)
        
    context = Context({
        "post": post,
    })

    return render_to_response(
        'home/framed.html', 
        context, 
        context_instance=RequestContext(request)
    )

def log_in_oauth(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/new')
    else:
        return render(request, 'home/log_in_oauth.html')

@login_required
def log_out(request):
    '''Log out a logged in user.'''
    logout(request)
    return HttpResponseRedirect('/')


@login_required
def add_blog(request):
    ''' Adds a new blog to a user's profile. '''

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

            # janky short circuit if they've already added this url
            for blog in Blog.objects.filter(user = request.user.id):
                if url == blog.url:
                    print "FOUND %s which matches %s" % (blog.url, url)
                    return HttpResponseRedirect('/new')

            # create new blog record in db
            blog = Blog.objects.create(
                                        user=User.objects.get(id=request.user.id),
                                        feed_url=feed_url,
                                        url=url,
                                        created=datetime.datetime.now(),
                                       )
            blog.save()

            # Feedergrabber returns ( [(link, title, date)], [errors])
            # We're not handling the errors returned for right now
            crawled, _ = feedergrabber27.feedergrabber(feed_url)

            # this try/except is a janky bugfix. This should be done with celery
            try:
                for post in crawled:
                    post_url, post_title, post_date = post
                    newpost = Post.objects.create(
                                                  blog=Blog.objects.get(user=request.user.id),
                                                  url=post_url,
                                                  title=post_title,
                                                  content="",
                                                  date_updated=post_date,
                                                  )
            except:
                pass

            return HttpResponseRedirect('/new')
        else:
            return HttpResponse("I didn't get your feed URL. Please go back and try again.")
    else:
        return render_to_response('home/add_blog.html', {}, context_instance=RequestContext(request))

@login_required
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

@login_required
def new(request, page=1):
    ''' Newest blog posts - main app view. '''

    # pagination handling
    items_per_page = 10
    if page is None or int(page) <= 0:
        start = 0
    else:
        start = (int(page) - 1)*items_per_page
    end = start + items_per_page
    pages = int(math.ceil(Post.objects.count()/float(items_per_page)))

    newPostList = Post.objects.order_by('-date_updated')[start:end]
    for post in newPostList:
        user            = User.objects.get(blog__id__exact=post.blog_id)
        post.author     = user.first_name + " " + user.last_name
        post.authorid   = user.id
        post.avatar     = Hacker.objects.get(user=user.id).avatar_url
        post.comments   = list(Comment.objects.filter(post=post))

    context = Context({
        "newPostList": newPostList,
        "page": int(page),
        "pages": pages,
    })

    return render_to_response('home/new.html',
                              context,
                              context_instance=RequestContext(request))

@login_required
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


@login_required
def item(request, slug):

    if request.method == 'POST':
        if request.POST['content']:
            comment = Comment.objects.create(
                slug         = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for x in range(6)),
                user            = request.user,
                post            = Post.objects.get(slug=slug),
                parent          = None,
                date_modified   = datetime.datetime.now(),
                content         = request.POST['content'],
            )
            comment.save()

    post = get_post_info(slug)

    commentList = get_comment_list(post)

    context = Context({
        "post": post,
        "commentList": commentList,
    })

    return render_to_response('home/item.html', context, context_instance=RequestContext(request))

def login_error(request):
    """OAuth error page"""
    return render(request, 'home/login_error.html')

# login NOT required
def about(request):
    """ About page with more info on Blaggregator. """
    return render(request, 'home/about.html')
