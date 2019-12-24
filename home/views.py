from collections import namedtuple
import datetime
from functools import wraps
import uuid

from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.forms import Select, TextInput
from django.forms.models import modelform_factory
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from home.models import Blog, Hacker, LogEntry, Post, STREAM_CHOICES
from home.oauth import update_user_details
from home.feeds import LatestEntriesFeed
from . import feedergrabber27

EXISTING_FEED_MESSAGE = ('This feed has already been added!')
NO_CONTENT_MESSAGE = (
    'Could not fetch feed from <a href="{url}">{url}</a>. Is the website up?'
)
INVALID_FEED_MESSAGE = (
    "This does not seem to be a valid feed. "
    "Please use your blog's feed url (not the web url)!"
)
SUGGEST_FEED_URL_MESSAGE = INVALID_FEED_MESSAGE + (
    ' It could be -- <a href="{url}">{url}</a>'
)
SUCCESS_MESSAGE = (
    'Your blog (<a href="{url}">{url}</a>) has been added successfully. '
    'The next crawl (hourly) will fetch your posts.'
)


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


def paginator(queryset, page_number, page_size=30):
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
    user_id = request.user.id
    # /add_blog in linked to in recurse.com, etc.
    if request.method == 'GET':
        return HttpResponseRedirect(
            reverse('profile', kwargs={'user_id': user_id})
        )

    feed_url = request.POST.get('feed_url', None)
    if feed_url:
        feed_url = feed_url.strip()
        # add http:// prefix if missing
        if feed_url[:4] != "http":
            feed_url = "http://" + feed_url
        # Check if the feed has already been added, and bail out
        user_blogs = Blog.objects.filter(user=user_id, feed_url=feed_url)
        if user_blogs.exists():
            user_blogs.update(skip_crawl=False)
            messages.info(request, EXISTING_FEED_MESSAGE)
            return HttpResponseRedirect(
                reverse('profile', kwargs={'user_id': user_id})
            )

        contents, errors = feedergrabber27.retrieve_file_contents(feed_url)
        if contents is None:  # URLError or HTTPError
            messages.error(
                request,
                NO_CONTENT_MESSAGE.format(url=feed_url),
                extra_tags='safe',
            )
        elif (
            contents.bozo and not isinstance(
                contents.bozo_exception,
                feedergrabber27.CharacterEncodingOverride,
            )
        ):  # Content failed to parse
            guessed_url = feedergrabber27.find_feed_url(contents)
            message = SUGGEST_FEED_URL_MESSAGE if guessed_url is not None else INVALID_FEED_MESSAGE
            messages.error(
                request, message.format(url=guessed_url), extra_tags='safe'
            )
        else:
            # create new blog record in db
            Blog.objects.create(
                user=User.objects.get(id=user_id), feed_url=feed_url
            )
            messages.success(
                request,
                SUCCESS_MESSAGE.format(url=feed_url),
                extra_tags='safe',
            )
    else:
        messages.error(request, "No feed URL provided.")
    return HttpResponseRedirect(
        reverse('profile', kwargs={'user_id': user_id})
    )


@login_required
@ensure_blog_exists
def delete_blog(request, blog_id):
    blog = request.blog
    user = request.user
    blog.delete()
    return HttpResponseRedirect(
        reverse('profile', kwargs={'user_id': user.id})
    )


@login_required
@ensure_blog_exists
@require_POST
def edit_blog(request, blog_id):
    blog = request.blog
    user = request.user
    form = BlogForm(request.POST, instance=blog)
    if form.is_valid():
        form.instance.skip_crawl = False
        form.save()
    return HttpResponseRedirect(
        reverse('profile', kwargs={'user_id': user.id})
    )


@login_required
@ensure_hacker_exists
def profile(request, user_id):
    added_blogs = Blog.objects.filter(user=user_id)
    owner = True if int(user_id) == request.user.id else False
    post_list = Post.objects.filter(blog__user=user_id)
    context = {
        'hacker': request.hacker,
        'owner': owner,
        'post_list': post_list,
        'show_avatars': False,
        'forms': [BlogForm(instance=blog) for blog in added_blogs],
    }
    return render(request, 'home/profile.html', context)


@login_required
def new(request):
    ''' Newest blog posts - main app view. '''
    posts = Post.objects.all()
    page = request.GET.get('page', 1)
    post_list = paginator(posts, page)
    context = {
        "post_list": post_list, 'show_avatars': True, "page_view": "new"
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
        "page_view": "search",
    }
    return render(request, 'home/search.html', context)


@login_required
@ensure_hacker_exists
def updated_avatar(request, user_id):
    update_user_details(user_id)
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
    streams = dict(STREAM_CHOICES)
    # Return a tab separated values file, if requested
    if request.GET.get('tsv') == '1':
        header = 'post_id\ttitle\turl\tcount\n'
        text = '\n'.join(_get_tsv(entry) for entry in entries)
        text = header + text
        response = HttpResponse(text, content_type='text/tab-separated-values')
    else:
        Post = namedtuple(
            'Post', ('authorid', 'avatar', 'slug', 'title', 'stream')
        )
        context = {
            'post_list': [
                Post(
                    slug=entry['post__slug'],
                    authorid=entry['post__blog__user__id'],
                    avatar=entry['post__blog__user__hacker__avatar_url'],
                    title=entry['post__title'],
                    stream=streams[entry['post__blog__stream']],
                )
                for entry in entries
            ],
            'from': since.date(),
            'to': now.date(),
            'show_avatars': True,
        }
        response = render(request, 'home/most_viewed.html', context)
    return response


def _get_most_viewed_entries(since, n=20):
    # Get posts visited during the last week
    entries = LogEntry.objects.filter(date__gte=since)
    # Get post url and title
    entries = entries.values(
        'post__id',
        'post__title',
        'post__url',
        'post__slug',
        'post__blog__user__id',
        'post__blog__user__hacker__avatar_url',
        'post__blog__stream',
    )
    # Count the visits
    entries = entries.annotate(total=Count('post__id'))
    # Get top 'n' posts
    entries = entries.order_by('total').reverse()[:n]
    return entries


def _get_tsv(entry):
    return '{post__id}\t{post__title}\t{post__url}\t{total}'.format(**entry)


BlogForm = modelform_factory(
    Blog,
    fields=("feed_url", "stream"),
    widgets={
        'feed_url': TextInput(attrs={'class': 'form-control', 'type': 'url'}),
        'stream': Select(attrs={'class': 'custom-select'}),
    },
)
