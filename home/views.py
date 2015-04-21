from collections import namedtuple
import datetime
import math
import re

from django.conf import settings
from django.contrib.auth import authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.forms import TextInput
from django.forms.models import modelform_factory
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, render
from django.template import Context, RequestContext
from django.utils import timezone

from home.models import Blog, Comment, generate_random_id, Hacker, LogEntry, Post
from home.oauth import update_user_details
import feedergrabber27

def get_post_info(slug):
    """ Gets the post object at a given slug. """

    try:
        post = Post.objects.get(slug=slug)
        user            = User.objects.get(blog__id__exact=post.blog_id)
        post.author     = user.first_name + " " + user.last_name
        post.authorid   = user.id
        post.avatar     = Hacker.objects.get(user=user.id).avatar_url
        post.slug       = slug

    except Post.DoesNotExist:
        raise Http404('Post does not exist.')

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


def view_post(request, slug):
    """Redirect to the original link.

    We use a redirect, so that we can collect stats if we decide to, and do
    useful things with it.

    """

    post = get_post_info(slug)
    LogEntry.objects.create(
        post=post,
        date=timezone.now(),
        referer=request.META.get('HTTP_REFERER', None),
        remote_addr=request.META.get('REMOTE_ADDR', None),
        user_agent=request.META.get('HTTP_USER_AGENT', None),
    )
    return HttpResponseRedirect(post.url)

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
                created=timezone.now(),
            )

            # Feedergrabber returns ( [(link, title, date)], [errors])
            # We're not handling the errors returned for right now
            crawled, _ = feedergrabber27.feedergrabber(feed_url)

            # this try/except is a janky bugfix. This should be done with celery
            try:
                for post_url, post_title, post_date, post_content in crawled:
                    Post.objects.create(
                        blog=blog,
                        url=post_url,
                        title=post_title,
                        content=post_content,
                        date_updated=timezone.make_aware(post_date, timezone.get_default_timezone()),
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
    """ A user's profile. Not currently tied to a template - needs work. """

    try:
        hacker = Hacker.objects.get(user=user_id)

    except Hacker.DoesNotExist:
        raise Http404

    else:
        added_blogs = Blog.objects.filter(user=user_id)
        owner = True if int(user_id) == request.user.id else False

        context = Context({
            'hacker': hacker,
            'blogs': added_blogs,
            'owner': owner,
        })

        response = render_to_response(
            'home/profile.html',
            context,
            context_instance=RequestContext(request)
        )

        return response

@login_required
def edit_blog(request, blog_id):

    try:
        user = request.user
        blog = Blog.objects.get(id=blog_id, user=user)
    except Blog.DoesNotExist:
        raise Http404

    BlogForm = modelform_factory(
        Blog,
        fields=("feed_url", "stream"),
        widgets={'feed_url': TextInput(attrs={'class': 'span6', 'type': 'url'})}
    )

    if request.method == 'POST':
        form = BlogForm(request.POST, instance=blog)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('profile', kwargs={'user_id': user.id}))

    form = BlogForm(instance=blog)

    context = Context({
        'blog': blog,
        'form': form
    })

    response = render_to_response(
        'home/edit_blog.html',
        context,
        context_instance=RequestContext(request)
    )

    return response

@login_required
def delete_blog(request, blog_id):

    try:
        user = request.user
        blog = Blog.objects.get(id=blog_id, user=user)
    except Blog.DoesNotExist:
        raise Http404

    blog.delete()

    return HttpResponseRedirect(reverse('profile', kwargs={'user_id': user.id}))


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
        post.comments   = list(Comment.objects.filter(post=post))
        post.avatar     = user.hacker.avatar_url

    context = Context({
        "newPostList": newPostList,
        "page": int(page),
        "pages": pages,
    })

    return render_to_response('home/new.html',
                              context,
                              context_instance=RequestContext(request))


@login_required
def updated_avatar(request, user_id):
    try:
        Hacker.objects.get(user=user_id)

    except Hacker.DoesNotExist:
        raise Http404

    else:
        update_user_details(user_id, request.user)
        hacker = Hacker.objects.get(user=user_id)

    return HttpResponse(hacker.avatar_url)


def feed(request):
    ''' Atom feed of all new posts. '''

    token = request.GET.get('token')
    if authenticate(token=token) is None:
        raise Http404

    postList = Post.objects.all().order_by('-date_updated')[:100]
    for post in postList:
        user = User.objects.get(blog__id__exact=post.blog_id)
        post.author = user.first_name + " " + user.last_name
        # fixme: also add the full content of the post to the feed.

    context = Context({
        "postList": postList,
        "domain": settings.SITE_URL
    })

    return render(request, 'home/atom.xml', context, content_type="text/xml")

@login_required
def refresh_token(request):
    """Refresh a users' auth token."""

    hacker = Hacker.objects.get(user=request.user)
    hacker.token = get_random_unique_token()
    hacker.save()

    profile_url = reverse('profile', kwargs={'user_id': request.user.id})
    return HttpResponseRedirect(profile_url)

def get_random_unique_token():
    """Get a random token after ensuring that it is unique.

    The model is passed as an argument to allow using this function in data
    migrations.

    """

    while True:
        token = generate_random_id(40)
        try:
            Hacker.objects.get(token=token)
        except Hacker.DoesNotExist:
            return token

@login_required
def item(request, slug):

    if request.method == 'POST':
        if request.POST['content']:
            Comment.objects.create(
                slug=generate_random_id(),
                user=request.user,
                post=Post.objects.get(slug=slug),
                parent=None,
                date_modified=timezone.now(),
                content=request.POST['content'],
            )

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


@login_required
def most_viewed(request):
    now = timezone.now()
    one_week = now - datetime.timedelta(days=7)
    entries = _get_most_viewed_entries(since=one_week)

    # Return a tab separated values file, if requested
    if request.GET.get('tsv') == '1':
        text = '\n'.join(_get_tsv(entry) for entry in entries)
        response = HttpResponse(text, content_type='text/tab-separated-values')

    else:
        Post = namedtuple('Post', ('authorid', 'avatar', 'slug', 'title'))
        context = {
            'post_list': [
                Post(
                    slug=entry['post__slug'],
                    authorid=entry['post__blog__user__id'],
                    avatar=entry['post__blog__user__hacker__avatar_url'],
                    title=entry['post__title'],
                )
                for entry in entries
            ],
            'from': one_week.date(),
            'to': now.date(),
        }
        response = render_to_response(
            'home/most_viewed.html', context
        )

    return response


def _get_most_viewed_entries(since, n=20):
    # Get posts visited during the last week
    entries = LogEntry.objects.filter(date__gte=since)

    # Get post url and title
    entries = entries.values(
        'post__id', 'post__title', 'post__url', 'post__slug',
        'post__blog__user__id', 'post__blog__user__hacker__avatar_url'
    )

    # Count the visits
    entries = entries.annotate(total=Count('post__id'))

    # Get top 'n' posts
    entries = entries.order_by('total').reverse()[:n]

    return entries


def _get_tsv(entry):
    return '{post__id}\t{post__title}\t{post__url}\t{total}'.format(**entry)
