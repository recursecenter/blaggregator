# Standard library
import os
import logging

# 3rd-party library
from django.core.urlresolvers import reverse
import requests

ZULIP_KEY = os.environ.get('ZULIP_KEY')
ZULIP_EMAIL = os.environ.get('ZULIP_EMAIL')
ZULIP_URL = 'https://recurse.zulipchat.com/api/v1/messages'

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
    content = "**{}** has a new blog post: [{}]({})".format(post.author, title, url)
    send_message_zulip(to, subject, content, type_='stream')


def send_message_zulip(to, subject, content, type_='private'):
    """Send a message to Zulip."""

    data = {
        "type": type_,
        "to": to,
        "subject": subject,
        "content": content,
    }

    try:
        log.debug('Sending message "%s" to %s (%s)', content, to, type_)
        response = requests.post(ZULIP_URL, data=data, auth=(ZULIP_EMAIL, ZULIP_KEY))
        log.debug('Post returned with %s: %s', response.status_code, response.content)
        return response

    except Exception as e:
        log.exception(e)
