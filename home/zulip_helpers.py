# Standard library
import logging
import os
from textwrap import dedent

# 3rd-party library
from django.conf import settings
from django.core.urlresolvers import reverse
import requests

# Local imports
from home.models import User

ZULIP_KEY = os.environ.get('ZULIP_KEY')
ZULIP_EMAIL = os.environ.get('ZULIP_EMAIL')
ZULIP_URL = 'https://recurse.zulipchat.com/api/v1/messages'
ANNOUNCE_MESSAGE = u"**{}** has a new blog post: [{}]({})"
SKIPPING_CRAWL_MESSAGE = dedent(
    u"""
    Hi {author},

    You added {url} as a Blaggregator feed. We are unable to parse it.
    Could you please update/remove it from [here]({profile_url})?

    If this appears to be a problem with Blaggregator, or you need help fixing
    this, please {contact}"""
)
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


def get_contact_info():
    """Returns contact info of staff, if present."""
    staff = [
        user.get_full_name()
        for user in User.objects.filter(is_staff=True).exclude(hacker=None)
    ]
    names = ' or '.join(
        filter(None, [', '.join(staff[:-1]), staff[-1]])
    ) if staff else ''
    message = (
        'get in touch with {}'.format(
            names
        ) if names else 'file an issue [here](https://github.com/recursecenter/blaggregator/issues)'
    )
    return message


def notify_uncrawlable_blog(blog, debug=True):
    """Notify blog owner about a blog that is failing crawls."""
    subject = 'Action required from Blaggregator'
    profile_path = reverse('profile', kwargs={'user_id': blog.user.id})
    profile_url = '{}/{}'.format(
        settings.ROOT_URL.rstrip('/'), profile_path.lstrip('/')
    )
    message = SKIPPING_CRAWL_MESSAGE
    content = message.format(
        author=blog.author,
        url=blog.feed_url,
        profile_url=profile_url,
        contact=get_contact_info(),
    )
    to = blog.user.email
    type_ = 'private'
    if debug:
        log.debug(u'Sending message \n\n%s\n\n to %s (%s)', content, to, type_)
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
    except Exception as e:
        log.exception(e)
