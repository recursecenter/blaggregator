# Standard library
from collections import deque
import logging
from optparse import make_option
import os

# 3rd-party library
from django.core.management.base import NoArgsCommand
from django.db import transaction
from django.utils import timezone
import requests

# Local library
from home.models import Blog, Post
from home import feedergrabber27

log = logging.getLogger("blaggregator")

ROOT_URL = 'https://blaggregator.recurse.com/'

STREAM = 'blogging'
MAX_POST_ANNOUNCE = 2

ZULIP_KEY = os.environ.get('ZULIP_KEY')
ZULIP_EMAIL = os.environ.get('ZULIP_EMAIL')
ZULIP_URL = 'https://recurse.zulipchat.com/api/v1/messages'


class Command(NoArgsCommand):

    help = 'Periodically crawls all blogs for new posts.'

    option_list = NoArgsCommand.option_list + (
        make_option('--dry-run',
                    action='store_true',
                    default=False,
                    help="Don't actually touch the database"),
    )

    # Queue up the messages for Zulip so they aren't sent until after the
    #   blog post instance is created in the database
    zulip_queue = deque()

    def crawlblog(self, blog):
        # Feedergrabber returns ( [(link, title, date)], [errors])
        # We're ignoring the errors returned for right now
        crawled, errors = feedergrabber27.feedergrabber(blog.feed_url)

        if not crawled:
            log.debug(str(errors))
            return

        log.debug('Crawled %s blogs from %s', len(crawled), blog.feed_url)

        for link, title, date, content in crawled:
            date = timezone.make_aware(date, timezone.get_default_timezone())
            title = cleantitle(title)

            # create the post instance if it doesn't already exist
            post, created = get_or_create_post(blog, title, link, date, content)

            if created:
                created_count = 0
                log.debug("Created '%s' from blog '%s'", title, blog.feed_url)

                # Throttle the amount of new posts that can be announced per
                # user per crawl.
                if created_count < MAX_POST_ANNOUNCE:
                    post_page = ROOT_URL + 'post/' + post.slug
                    self.enqueue_zulip(blog.user, post_page, title, blog.stream)
                    created_count += 1

            # if title changes, update the post
            elif title != post.title or content != post.content:
                post.title = title
                post.content = content
                print "Updated %s in %s." % (title, blog.feed_url)
                post.save()

            else:
                # Any other updates are ignored, as of now
                pass

    @transaction.commit_manually
    def handle_noargs(self, **options):
        for blog in Blog.objects.all():
            try:
                self.crawlblog(blog)
            except Exception as e:
                log.exception(e)
        if options['dry_run']:
            transaction.rollback()
            print "\nDON'T FORGET TO RUN THIS FOR REAL\n"
        else:
            for message in self.zulip_queue:
                user, link, title, stream = message
                send_message_zulip(user, link, title, stream)
            transaction.commit()

    def enqueue_zulip(self, user, link, title, stream=STREAM):
        self.zulip_queue.append((user, link, title, stream))


def cleantitle(title):
    ''' Strip the blog title of newlines. '''

    newtitle = ''

    for char in title:
        if char != '\n':
            newtitle += char

    return newtitle


def get_or_create_post(blog, title, link, date, content):
    try:
        # The previous code checked only for url, and therefore, the db can
        # have posts with duplicate titles. So, we check if there is atleast
        # one post with the title -- using `filter.latest` instead of `get`.
        post = Post.objects.filter(blog=blog, title=title).latest('date_posted_or_crawled')
        return post, False
    except Post.DoesNotExist:
        pass

    try:
        post = Post.objects.get(blog=blog, url=link)
        return post, False

    except Post.DoesNotExist:
        post, created = Post.objects.get_or_create(
            blog=blog,
            url=link,
            defaults={
                'title': title,
                'date_posted_or_crawled': date,
                'content': content,
            }
        )

    return post, created


def send_message_zulip(user, link, title, stream=STREAM):
    """Announce new post with given link and title by user on specified stream."""

    subject = title if len(title) <= 60 else title[:57] + "..."
    url = "{0}/view".format(link.rstrip('/'))
    data = {
        "type": "stream",
        "to": "%s" % stream,
        "subject": subject,
        "content": "**%s %s** has a new blog post: [%s](%s)" % (user.first_name, user.last_name, title, url),
    }

    try:
        log.debug('Sending data %s to zulip stream %s', data['content'], stream)
        response = requests.post(ZULIP_URL, data=data, auth=(ZULIP_EMAIL, ZULIP_KEY))
        log.debug('Post returned with %s: %s', response.status_code, response.content)

    except Exception as e:
        log.exception(e)

    return response
