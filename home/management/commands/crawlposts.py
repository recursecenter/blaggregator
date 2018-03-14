# Standard library
from collections import deque
import logging

# 3rd-party library
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

# Local library
from home import feedergrabber27
from home.models import Blog, Post
from home.zulip_helpers import announce_new_post

log = logging.getLogger("blaggregator")


class Command(BaseCommand):
    help = 'Periodically crawls all blogs for new posts.'
    # Queue up the messages for Zulip so they aren't sent until after the
    #   blog post instance is created in the database
    zulip_queue = deque()

    def crawlblog(self, blog):
        # Feedergrabber returns ( [(link, title, content)], [errors])
        # We're ignoring the errors returned for right now
        crawled, errors = feedergrabber27.feedergrabber(blog.feed_url)
        if not crawled:
            log.debug(str(errors))
            return

        log.debug('Crawled %s posts from %s', len(crawled), blog.feed_url)
        blog.last_crawled = timezone.now()
        blog.save(update_fields=['last_crawled'])
        created_count = 0
        for link, title, content in crawled:
            # create the post instance if it doesn't already exist
            post, created = get_or_create_post(blog, title, link, content)
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
        for blog in Blog.objects.all():
            try:
                self.crawlblog(blog)
            except Exception as e:
                log.exception(e)
        for post in self.zulip_queue:
            announce_new_post(post, debug=settings.DEBUG)


def get_or_create_post(blog, title, link, content):
    try:
        # The previous code checked only for url, and therefore, the db can
        # have posts with duplicate titles. So, we check if there is atleast
        # one post with the title -- using `filter.latest` instead of `get`.
        post = Post.objects.filter(blog=blog, title=title).latest('created_at')
        return post, False

    except Post.DoesNotExist:
        pass
    post, created = Post.objects.get_or_create(
        blog=blog, url=link, defaults={'title': title, 'content': content}
    )
    return post, created


def update_post(post, title, link, content):
    """Update a post with the new content."""
    if post.title == title and post.url == link and post.content == content:
        return

    post.title = title
    post.url = link
    post.content = content
    post.save()
    log.debug("Updated %s - %s.", title, link)
