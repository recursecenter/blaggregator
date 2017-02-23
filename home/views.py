from collections import namedtuple
import datetime
from functools import wraps
import re
import uuid

from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.forms import TextInput
from django.forms.models import modelform_factory
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.utils import timezone

from home.models import Blog, Hacker, LogEntry, Post
from home.oauth import update_user_details
from home.feeds import LatestEntriesFeed
import feedergrabber27


def ensure_blog_exists(f):
    @wraps(f)
    def wrapper(request, blog_id):
        try:
            blog = Blog.objects.get(id=blog_id, user=request.user)
            request.blog = blog
        except Blog.DoesNotExist:
            raise Http404
        return f(request, blog_id)
    return wrapper


def ensure_hacker_exists(f):
    @wraps(f)
    def wrapper(request, user_id):
        try:
            hacker = Hacker.objects.get(user=user_id)
        except Hacker.DoesNotExist:
            raise Http404
        request.hacker = hacker
        return f(request, user_id)
    return wrapper


def paginator(queryset, page_number, page_size=10):
    paginator = Paginator(queryset, page_size)
    try:
        items = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)

    return items


def view_post(request, slug):
    """Redirect to the original link.

    We use a redirect, so that we can collect stats if we decide to, and do
    useful things with it.

    """

    try:
        post = Post.objects.get(slug=slug)

    except Post.DoesNotExist:
        raise Http404('Post does not exist.')

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
        return HttpResponseRedirect(reverse('new'))
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
        feed_url = request.POST.get('feed_url', None)
        if feed_url:
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
            for blog in Blog.objects.filter(user=request.user.id):
                if url == blog.url:
                    print "FOUND %s which matches %s" % (blog.url, url)
                    return HttpResponseRedirect(reverse('new'))

            # Feedergrabber returns ( [(link, title, date)], [errors])
            # We're not handling the errors returned for right now
            # Returns None if there was an exception when parsing the content.
            crawled, errors = feedergrabber27.feedergrabber(feed_url, suggest_feed_url=True)
            if crawled is None:
                message = (
                    "This url does not seem to contain valid atom/rss feed xml. "
                    "Please use your blog's feed url! "
                )

                if errors and len(errors) == 1 and isinstance(errors[0], dict) and 'feed_url' in errors[0]:
                    feed_url = errors[0]['feed_url']
                    if feed_url is not None:
                        message += 'It may be this -- {}'.format(feed_url)

                messages.error(request, message)
                return HttpResponseRedirect(reverse('add_blog'))

            # create new blog record in db
            blog = Blog.objects.create(
                user=User.objects.get(id=request.user.id),
                feed_url=feed_url,
                url=url,
            )

            # FIXME: this try/except is a janky bugfix. Use celery instead?
            # FIXME: very similar to code in crawlposts.get_or_create_post
            try:
                for post_url, post_title, post_date, post_content in crawled:
                    post_date = timezone.make_aware(post_date, timezone.get_default_timezone())
                    Post.objects.create(
                        blog=blog,
                        url=post_url,
                        title=post_title,
                        content=post_content,
                        date_posted_or_crawled=post_date,
                    )
            except Exception as e:
                print e

            return HttpResponseRedirect(reverse('new'))
        else:
            messages.error(request, "No feed URL provided.")
            return HttpResponseRedirect(reverse('add_blog'))
    else:
        return render(request, 'home/add_blog.html')


@login_required
@ensure_blog_exists
def delete_blog(request, blog_id):

    blog = request.blog
    user = request.user
    blog.delete()
    return HttpResponseRedirect(reverse('profile', kwargs={'user_id': user.id}))


@login_required
@ensure_blog_exists
def edit_blog(request, blog_id):

    blog = request.blog
    user = request.user
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
    context = {'blog': blog, 'form': form}
    return render(request, 'home/edit_blog.html', context)


@login_required
@ensure_hacker_exists
def profile(request, user_id):
    added_blogs = Blog.objects.filter(user=user_id)
    owner = True if int(user_id) == request.user.id else False

    post_list = Post.objects.filter(blog__user=user_id).order_by('-date_posted_or_crawled')

    context = {
        'hacker': request.hacker,
        'blogs': added_blogs,
        'owner': owner,
        'post_list': post_list,
        'show_avatars': False,
    }
    return render(request, 'home/profile.html', context)


@login_required
def new(request):
    ''' Newest blog posts - main app view. '''

    posts = Post.objects.order_by('-date_posted_or_crawled')
    page = request.GET.get('page', 1)
    post_list = paginator(posts, page)

    context = {
        "post_list": post_list,
        'show_avatars': True,
        "page_view": "new"
    }
    return render(request, 'home/new.html', context)


@login_required
def search(request):
    ''' Search blog posts based on query - main app view. '''

    query = request.GET.get('q', '')
    posts = Post.objects.filter(title__search=query)
    count = posts.count()
    page = request.GET.get('page', 1)
    post_list = paginator(posts, page)

    context = {
        "count": count,
        "query": query,
        "post_list": post_list,
        'show_avatars': True,
        "page_view": "search"
    }

    return render(request, 'home/search.html', context)


@login_required
@ensure_hacker_exists
def updated_avatar(request, user_id):
    update_user_details(user_id, request.user)
    hacker = Hacker.objects.get(user=user_id)
    return HttpResponse(hacker.avatar_url)


# FIXME: This view could be cached, with cache cleared on crawls or Blog
# create/delete signals.  Probably most other views could be cached.
def feed(request):
    """Atom feed of new posts."""

    token = request.GET.get('token')
    if authenticate(token=token) is None:
        raise Http404

    return LatestEntriesFeed()(request)


@login_required
def refresh_token(request):
    """Refresh a users' auth token."""

    hacker = Hacker.objects.get(user=request.user)
    hacker.token = uuid.uuid4().hex
    hacker.save()

    profile_url = reverse('profile', kwargs={'user_id': request.user.id})
    return HttpResponseRedirect(profile_url)


@login_required
def login_error(request):
    """OAuth error page"""
    return render(request, 'home/login_error.html')


# login NOT required
def about(request):
    """ About page with more info on Blaggregator. """
    return render(request, 'home/about.html')


@login_required
def most_viewed(request, ndays='7'):
    now = timezone.now()
    ndays = int(ndays)
    since = now - datetime.timedelta(days=ndays)
    entries = _get_most_viewed_entries(since=since)

    # Return a tab separated values file, if requested
    if request.GET.get('tsv') == '1':
        header = 'post_id\ttitle\turl\tcount\n'
        text = '\n'.join(_get_tsv(entry) for entry in entries)
        text = header + text
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
            'from': since.date(),
            'to': now.date(),
        }
        response = render(request, 'home/most_viewed.html', context)

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
    return u'{post__id}\t{post__title}\t{post__url}\t{total}'.format(**entry)
