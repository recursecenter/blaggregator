from collections import namedtuple
import datetime
import math
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
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

from home.models import Blog, Hacker, LogEntry, Post
from home.oauth import update_user_details
import feedergrabber27


def get_post_info(slug):
    """ Gets the post object at a given slug. """

    try:
        post = Post.objects.get(slug=slug)
        user = User.objects.get(blog__id__exact=post.blog_id)
        post.author = user.first_name + " " + user.last_name
        post.authorid = user.id
        post.avatar = Hacker.objects.get(user=user.id).avatar_url
        post.slug = slug

    except Post.DoesNotExist:
        raise Http404('Post does not exist.')

    return post


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
            except:
                pass

            return HttpResponseRedirect(reverse('new'))
        else:
            messages.error(request, "No feed URL provided.")
            return HttpResponseRedirect(reverse('add_blog'))
    else:
        return render_to_response('home/add_blog.html', {}, context_instance=RequestContext(request))


@login_required
def profile(request, user_id):

    try:
        hacker = Hacker.objects.get(user=user_id)

    except Hacker.DoesNotExist:
        raise Http404

    else:
        added_blogs = Blog.objects.filter(user=user_id)
        owner = True if int(user_id) == request.user.id else False

        post_list = Post.objects.filter(blog__user=user_id).order_by('-date_posted_or_crawled')
        for post in post_list:
            post.stream = post.blog.get_stream_display()

        context = Context({
            'hacker': hacker,
            'blogs': added_blogs,
            'owner': owner,
            'post_list': post_list,
            'show_avatars': False,
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
        start = (int(page) - 1) * items_per_page
    end = start + items_per_page
    pages = int(math.ceil(Post.objects.count() / float(items_per_page)))

    post_list = Post.objects.order_by('-date_posted_or_crawled')[start:end]
    for post in post_list:
        user = User.objects.get(blog__id__exact=post.blog_id)
        post.author = user.first_name + " " + user.last_name
        post.authorid = user.id
        post.avatar = user.hacker.avatar_url
        post.stream = post.blog.get_stream_display()

    context = Context({
        "post_list": post_list,
        "page": int(page),
        "pages": pages,
        'show_avatars': True,
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


@login_required
def feed(request):
    ''' Atom feed of all new posts. '''

    postList = list(Post.objects.all().order_by('-date_posted_or_crawled'))

    for post in postList:
        user = User.objects.get(blog__id__exact=post.blog_id)
        post.author = user.first_name + " " + user.last_name

    context = Context({
        "postList": postList,
        "domain": settings.SITE_URL
    })

    return render(request, 'home/atom.xml', context, content_type="text/xml")


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
    return u'{post__id}\t{post__title}\t{post__url}\t{total}'.format(**entry)
