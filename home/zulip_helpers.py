# Standard library
import os
import logging

# 3rd-party library
import requests

ZULIP_KEY = os.environ.get('ZULIP_KEY')
ZULIP_EMAIL = os.environ.get('ZULIP_EMAIL')
ZULIP_URL = 'https://recurse.zulipchat.com/api/v1/messages'

log = logging.getLogger("blaggregator")


def send_message_zulip(user, link, title, to):
    """Announce new post with given link and title by user on specified stream."""

    subject = title if len(title) <= 60 else title[:57] + "..."
    url = "{0}/view".format(link.rstrip('/'))
    data = {
        "type": "stream",
        "to": to,
        "subject": subject,
        "content": "**{} {}** has a new blog post: [{}]({})".format(
            user.first_name, user.last_name, title, url
        ),
    }

    try:
        log.debug('Sending data %s to zulip stream %s', data['content'], data['to'])
        response = requests.post(ZULIP_URL, data=data, auth=(ZULIP_EMAIL, ZULIP_KEY))
        log.debug('Post returned with %s: %s', response.status_code, response.content)
        return response

    except Exception as e:
        log.exception(e)
