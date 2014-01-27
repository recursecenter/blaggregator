from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction
from django.utils import timezone
from optparse import make_option
from home.models import Blog, Post
from home import feedergrabber27
import logging
import requests
import os
import datetime

log = logging.getLogger("blaggregator")

ROOT_URL = 'http://www.blaggregator.us/'

STREAM = 'blogging'

# am too lazy to change these variable names from humbug to zulip. sorry, jessica! 
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

        # Feedergrabber returns ( [(link, title, date)], [errors])
        # We're ignoring the errors returned for right now
        crawled, errors = feedergrabber27.feedergrabber(blog.feed_url)

        if crawled:

            for link, title, date in crawled:

                date = timezone.make_aware(date, timezone.get_default_timezone())
                now = timezone.make_aware(datetime.datetime.now(), timezone.get_default_timezone())

                title = cleantitle(title)

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
                    print "Created '%s' from blog '%s'" % (title, blog.feed_url)
                    # Only post to zulip if the post was created in the last 2 days
                    #   so that new accounts don't spam zulip with their entire post list
                    if (now - date) < datetime.timedelta(days=2):
                        post_page = ROOT_URL + 'post/' + Post.objects.get(url=link).slug
                        send_message_zulip(user=blog.user, link=post_page, title=title)
                        
                    # subscribe the author to comment updates
                    subscription, created = Comment_Subscription.objects.get_or_create(
                        user = blog.user,
                        post = post,
                    )

                # if new info, update the posts
                if not created:
                    # print ".",
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
            transaction.commit()


def cleantitle(title):
    ''' Strip the blog title of newlines. '''

    newtitle = ''

    for char in title:
        if char != '\n':
            newtitle += char

    return newtitle


def send_message_zulip(user, link, title):

    subject = title
    if len(subject) > 60:
        subject = subject[:57] + "..."
    
    # add a trailing slash if it's not already there (jankily)
    if link[-1] != '/': link = link + '/'
    url = link + "view"
    data = {"type": "stream",
            "to": "%s" % STREAM,
            "subject": subject,
            "content": "**%s** has a new blog post: [%s](%s)" % (user.first_name, title, url),
        }
    print data['content']
    r = requests.post('https://api-zulip-com-y3ee336dh1kn.runscope.net/v1/messages', data=data, auth=(email, key))
