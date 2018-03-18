# Standard library
import logging
import os
import re

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
MESSAGES_URL = 'https://recurse.zulipchat.com/api/v1/messages'
MEMBERS_URL = 'https://recurse.zulipchat.com/api/v1/users'
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


def notify_uncrawlable_blogs(user, blogs, debug=True):
    """Notify blog owner about blogs that are failing crawls."""
    subject = 'Blaggregator: Action required!'
    admins = User.objects.filter(is_staff=True).exclude(hacker=None)
    names = get_text_list([admin.get_full_name() for admin in admins], 'or')
    context = dict(
        user=user,
        blogs=blogs,
        base_url=settings.ROOT_URL.rstrip('/'),
        admins=names,
    )
    content = get_template('home/disabling-crawling.md').render(context)
    to = getattr(user, 'zulip_email', user.email)
    type_ = 'private'
    if debug:
        log.debug(u'Sending message \n\n%s\n\n to %s (%s)', content, to, type_)
        return False

    else:
        return send_message_zulip(to, subject, content, type_=type_)


def send_message_zulip(to, subject, content, type_='private'):
    """Send a message to Zulip."""
    data = {"type": type_, "to": to, "subject": subject, "content": content}
    try:
        log.debug(u'Sending message "%s" to %s (%s)', content, to, type_)
        response = requests.post(
            MESSAGES_URL, data=data, auth=(ZULIP_EMAIL, ZULIP_KEY)
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


def guess_zulip_emails(users):
    """Get zulip emails for users

    Some users may not have the same email ids on zulip and recurse.com, in
    which case sending private messages will fail. This function tries to
    detect the zulip email based on the full name of the user.

    *NOTE*: The email in our DB is not changed. The email is temporarily set as
     an attribute on the user, so that notifications can be sent to the user.

    """
    try:
        response = requests.get(MEMBERS_URL, auth=(ZULIP_EMAIL, ZULIP_KEY))
        members = response.json()['members']
    except Exception as e:
        log.error('Could not fetch zulip users: %s', e)
    NAMES = {
        strip_batch(member['full_name']): member['email']
        for member in members
        if not member['is_bot'] and member['is_active']
    }
    EMAILS = {email: name for name, email in NAMES.items()}
    for user in users:
        if user.email not in EMAILS and user.get_full_name() in NAMES:
            user.zulip_email = NAMES[user.get_full_name()]
        else:
            # Either the email is correct OR
            # Both name and email have changed or account deleted!
            pass
    return users


def strip_batch(name):
    """Strip parenthesized batch from a name"""
    return re.sub('\(.*\)', '', name).strip()
