# Standard library
import logging
import os

# 3rd-party library
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.utils.text import get_text_list
import requests

# Local imports
from home.models import User

ZULIP_KEY = os.environ.get('ZULIP_KEY')
ZULIP_EMAIL = os.environ.get('ZULIP_EMAIL')
ZULIP_URL = 'https://recurse.zulipchat.com/api/v1/messages'
ANNOUNCE_MESSAGE = u"**{}** has a new blog post: [{}]({})"
log = logging.getLogger("blaggregator")


def announce_new_post(post, debug=True):
    """Announce new post on the correct stream.

    *NOTE*: If DEBUG mode is on, all messages are sent to the bot-test stream.

    """
    to = post.blog.get_stream_display() if not debug else 'bot-test'
    title = post.title
    subject = title if len(title) <= 60 else title[:57] + "..."
    path = reverse('view_post', kwargs={'slug': post.slug})
    url = '{}/{}'.format(settings.ROOT_URL.rstrip('/'), path.lstrip('/'))
    content = ANNOUNCE_MESSAGE.format(post.author, title, url)
    send_message_zulip(to, subject, content, type_='stream')


def notify_uncrawlable_blog(blog, debug=True):
    """Notify blog owner about a blog that is failing crawls."""
    subject = 'Action required from Blaggregator'
    admins = User.objects.filter(is_staff=True).exclude(hacker=None)
    names = get_text_list([admin.get_full_name() for admin in admins], 'or')
    context = dict(
        user=blog.user,
        blog=blog,
        base_url=settings.ROOT_URL.rstrip('/'),
        admins=names,
    )
    content = get_template('home/disabling-crawling.md').render(context)
    to = blog.user.email
    type_ = 'private'
    if debug:
        log.debug(u'Sending message \n\n%s\n\n to %s (%s)', content, to, type_)
        return True

    else:
        send_message_zulip(to, subject, content, type_=type_)


def send_message_zulip(to, subject, content, type_='private'):
    """Send a message to Zulip."""
    data = {"type": type_, "to": to, "subject": subject, "content": content}
    try:
        log.debug(u'Sending message "%s" to %s (%s)', content, to, type_)
        response = requests.post(
            ZULIP_URL, data=data, auth=(ZULIP_EMAIL, ZULIP_KEY)
        )
        log.debug(
            u'Post returned with %s: %s',
            response.status_code,
            response.content,
        )
        return response.status_code == 200

    except Exception as e:
        log.exception(e)
        return False
