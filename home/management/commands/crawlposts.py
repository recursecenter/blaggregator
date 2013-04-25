from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction
from django.utils import timezone
from optparse import make_option
from home.models import Blog, Post
from home import feedergrabber27
import logging
import requests
import os

log = logging.getLogger("blaggregator")

key = os.environ.get('HUMBUG_KEY')
email = os.environ.get('HUMBUG_EMAIL')

class Command(NoArgsCommand):
    help = 'Periodically crawls all blogs for new posts.'

    option_list = NoArgsCommand.option_list + (
        make_option('--dry-run',
            action = 'store_true',
            default = False,
            help = 'Don\'t actually touch the database',
            ),
        )

    def crawlblog(self, blog):

        print "** CRAWLING", blog.feed_url

        # Feedergrabber returns ( [(link, title, date)], [errors])
        # We're ignoring the errors returned for right now
        crawled, errors = feedergrabber27.feedergrabber(blog.feed_url)

        if crawled:

            for link, title, date in crawled:

                date = timezone.make_aware(date, timezone.get_default_timezone())

                # create the post instance if it doesn't already exist
                post, created = Post.objects.get_or_create(
                    blog = blog,
                    url = link,
                    defaults = {
                        'title': title,
                        'date_updated': date,
                    }
                )

                if created:
                    print "Created", title
                    send_message_hb(user=blog.user, link=link, title=title)

                # if new info, update the posts
                if not created:
                    print "Retrieved", title
                    updated = False
                    if date != post.date_updated:
                        post.date_updated = date
                        updated = True
                    if title != post.title:
                        post.title = title
                        updated = True
                    if updated:
                        print "Updated", title
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
            transaction.commit()

def send_message_hb(user, link, title):

    data = {"type": "stream",
            "to": "announce",
            "subject": "new blog post",
            "content": "**%s** has a new blog post: [%s](%s)" % (user.first_name, title, link)
        }

    r = requests.post('https://humbughq.com/api/v1/messages', data=data, auth=(email, key))

