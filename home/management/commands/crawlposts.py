# Patch everything as early as possible.
import gevent.monkey

# We turn off patching threading, since we don't really need it. If not, we get
# a KeyError on threading shutdown.
# See http://stackoverflow.com/a/12639040 for an explanation of the exception.
gevent.monkey.patch_all(thread=False)
# Standard library
from collections import deque  # noqa
import logging  # noqa

# 3rd-party library
from django.core.management.base import BaseCommand  # noqa
from django.conf import settings  # noqa
from django.utils import timezone  # noqa
from gevent import pool, wait  # noqa

# Local library
from home import feedergrabber27  # noqa
from home.models import Blog, Post  # noqa
from home.zulip_helpers import announce_new_post  # noqa

log = logging.getLogger("blaggregator")


class Command(BaseCommand):
    help = 'Periodically crawls all blogs for new posts.'
    # Queue up the messages for Zulip so they aren't sent until after the
    #   blog post instance is created in the database
    zulip_queue = deque()

    def crawlblog(self, blog):
        # Feedergrabber returns ( [(link, title, date, content)], [errors])
        crawled, errors = feedergrabber27.feedergrabber(blog.feed_url)
        if not crawled:
            log.debug('\n'.join(errors))
            return

        log.debug('Crawled %s posts from %s', len(crawled), blog.feed_url)
        if errors:
            log.debug('\n'.join(errors))
        blog.last_crawled = timezone.now()
        blog.save(update_fields=['last_crawled'])
        created_count = 0
        for link, title, date, content in crawled:
            date = timezone.make_aware(date, timezone.get_default_timezone())
            # create the post instance if it doesn't already exist
            post, created = get_or_create_post(
                blog, title, link, date, content
            )
            if created:
                created_count += 1
                log.debug("Created '%s' from blog '%s'", title, blog.feed_url)
                # Throttle the amount of new posts that can be announced per
                # user per crawl.
                if created_count <= settings.MAX_POST_ANNOUNCE:
                    self.zulip_queue.append(post)
            else:
                update_post(post, title, link, content)

    def handle(self, **options):
        p = pool.Pool(20)
        jobs = [
            p.spawn(self.crawlblog, blog)
            for blog in Blog.objects.filter(skip_crawl=False)
        ]
        wait(jobs)
        for post in self.zulip_queue:
            announce_new_post(post, debug=settings.DEBUG)


def get_or_create_post(blog, title, link, date, content):
    try:
        # The previous code checked only for url, and therefore, the db can
        # have posts with duplicate titles. So, we check if there is atleast
        # one post with the title -- using `filter.latest` instead of `get`.
        post = Post.objects.filter(blog=blog, title=title).latest('posted_at')
        return post, False

    except Post.DoesNotExist:
        pass
    post, created = Post.objects.get_or_create(
        blog=blog,
        url=link,
        defaults={'title': title, 'posted_at': date, 'content': content},
    )
    return post, created


def update_post(post, title, link, content):
    """Update a post with the new content.

    Updates if title, link or content has changed. Date is ignored since it may
    not always be parsed correctly, and we sometimes just use datetime.now()
    when parsing feeds.

    """
    if post.title == title and post.url == link and post.content == content:
        return

    post.title = title
    post.url = link
    post.content = content
    post.save()
    log.debug("Updated %s - %s.", title, link)
