from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction
from django.utils import timezone
from optparse import make_option
from home.models import Blog, Post
from home import feedergrabber27
from collections import deque
import logging
import requests
import os
import datetime

log = logging.getLogger("blaggregator")

ROOT_URL = 'http://www.blaggregator.us/'

STREAM = 'blogging'
MAX_POST_ANNOUNCE = 2

key = os.environ.get('HUMBUG_KEY')
email = os.environ.get('HUMBUG_EMAIL')
rs_bucket = os.environ.get('RUNSCOPE_BUCKET')
rs_url = 'https://api-zulip-com-{0}.runscope.net/v1/messages'.format(rs_bucket)

class Command(NoArgsCommand):

    help = 'Periodically crawls all blogs for new posts.'

    option_list = NoArgsCommand.option_list + (
        make_option('--dry-run',
            action = 'store_true',
            default = False,
            help = 'Don\'t actually touch the database',
            ),
        )

    # Queue up the messages for Zulip so they aren't sent until after the
    #   blog post instance is created in the database
    zulip_queue = deque()

    def crawlblog(self, blog):
        # Feedergrabber returns ( [(link, title, date)], [errors])
        # We're ignoring the errors returned for right now
        crawled, errors = feedergrabber27.feedergrabber(blog.feed_url)

        if crawled:
            post_count = 0
            for link, title, date, content in crawled:

                date = timezone.make_aware(date, timezone.get_default_timezone())
                now = timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone())

                title = cleantitle(title)

                # create the post instance if it doesn't already exist
                post, created = Post.objects.get_or_create(
                    blog=blog,
                    url=link,
                    defaults={
                        'title': title,
                        'date_updated': date,
                        'content': content,
                    }
                )

                if created:
                    print "Created '%s' from blog '%s'" % (title, blog.feed_url)

                    # Throttle the amount of new posts that can be announced per user per crawl.
                    if post_count < MAX_POST_ANNOUNCE:
                        post_page = ROOT_URL + 'post/' + Post.objects.get(url=link).slug
                        self.enqueue_zulip(self.zulip_queue, blog.user, post_page, title, blog.stream)
                        post_count += 1

                # if new info, update the posts
                if not created:
                    updated = False
                    if date != post.date_updated:
                        post.date_updated = date
                        updated = True
                    if title != post.title:
                        post.title = title
                        updated = True
                    if updated:
                        print "Updated %s in %s." % (title, blog.feed_url)
                        post.save()

        else:
            log.debug(str(errors))


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

    def enqueue_zulip(self, queue, user, link, title, stream=STREAM):
        self.zulip_queue.append((user, link, title, stream))


def cleantitle(title):
    ''' Strip the blog title of newlines. '''

    newtitle = ''

    for char in title:
        if char != '\n':
            newtitle += char

    return newtitle


def send_message_zulip(user, link, title, stream=STREAM):

    subject = title
    if len(subject) > 60:
        subject = subject[:57] + "..."

    # add a trailing slash if it's not already there (jankily)
    if link[-1] != '/': link = link + '/'
    url = link + "view"
    data = {"type": "stream",
            "to": "%s" % stream,
            "subject": subject,
            "content": "**%s %s** has a new blog post: [%s](%s)" % (user.first_name, user.last_name, title, url),
        }
    print data['content']
    r = requests.post(rs_url, data=data, auth=(email, key))
