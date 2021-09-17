# Standard library
import json
import logging
import os
import re

# 3rd-party library
from django.conf import settings
from django.template.loader import get_template
from django.urls import reverse
import requests

from home.models import Hacker, Post
from home.oauth import update_user_details

ZULIP_KEY = os.environ.get("ZULIP_KEY")
ZULIP_EMAIL = os.environ.get("ZULIP_EMAIL")
MESSAGES_URL = "https://recurse.zulipchat.com/api/v1/messages"
MEMBERS_URL = "https://recurse.zulipchat.com/api/v1/users"
ANNOUNCE_MESSAGE = "{} has a new blog post: [{}]({})"
log = logging.getLogger("blaggregator")


def announce_posts(posts, debug=True):
    """Announce new posts on the correct stream.

    *NOTE*: If DEBUG mode is on, all messages are sent to the bot-test stream.

    """

    if not posts:
        log.debug("No posts to announce")
        return

    author_zulip_ids = get_author_zulip_ids(posts)
    zulip_members = get_members()["by_id"]

    for post in posts:
        author_zulip_id = author_zulip_ids.get(post.id)
        author_name = zulip_members.get(author_zulip_id, {}).get("full_name")
        author = f"@**{author_name}**" if author_name else f"**{post.author}**"
        to = post.blog.get_stream_display() if not debug else "bot-test"
        title = post.title
        subject = title if len(title) <= 60 else title[:57] + "..."
        path = reverse("view_post", kwargs={"slug": post.slug})
        url = "{}/{}".format(settings.ROOT_URL.rstrip("/"), path.lstrip("/"))
        content = ANNOUNCE_MESSAGE.format(author, title, url)
        send_message_zulip(to, subject, content, type_="stream")


def delete_message(message_id, content="(deleted)"):
    message_url = "{}/{}".format(MESSAGES_URL, message_id)
    params = {"content": content, "subject": content}
    try:
        response = requests.patch(message_url, params=params, auth=(ZULIP_EMAIL, ZULIP_KEY))
        assert response["result"] == "success"
    except Exception as e:
        log.error("Could not delete Zulip message %s: %s", message_id, e)


def get_author_zulip_ids(posts):
    """Return mapping of post ID to author Zulip ID.

    NOTE: The function also tries to update the Zulip IDs of users that are not
    in our DB using data from the RC API end-point: /api/v1/profiles/:id

    """

    post_ids = {post.id for post in posts}
    author_zulip_ids = dict(
        Post.objects.filter(pk__in=post_ids).values_list(
            "blog__user", "blog__user__hacker__zulip_id"
        )
    )

    for user_id, zulip_id in author_zulip_ids.items():
        if zulip_id is None:
            update_user_details(user_id)
            hacker = Hacker.objects.filter(user_id=user_id).first()
            if hacker is not None and hacker.zulip_id is not None:
                author_zulip_ids[user_id] = hacker.zulip_id
                log.debug("Updated Zulip ID for hacker %s", user_id)
            else:
                log.error("Failed to update Zulip ID for hacker %s", user_id)

    return {post.id: author_zulip_ids.get(post.blog.user_id) for post in posts}


def get_members():
    """Returns info of all the Zulip users.

    Returns a mapping with three keys - by_name, by_email and by_id.

    """
    try:
        log.debug("Fetching all Zulip members")
        response = requests.get(MEMBERS_URL, auth=(ZULIP_EMAIL, ZULIP_KEY))
        members = response.json()["members"]
    except Exception as e:
        log.error("Could not fetch zulip users: %s", e)
        members = []
    by_name = {
        strip_batch(member["full_name"]): member
        for member in members
        if not member["is_bot"] and member["is_active"]
    }
    by_email = {member["email"]: member for member in by_name.values()}
    by_id = {member["user_id"]: member for member in by_name.values()}
    return dict(by_email=by_email, by_name=by_name, by_id=by_id)


def get_pm_link(user, members):
    """Returns a zulip link for PM with a user."""
    name = user.get_full_name()
    first_name = user.first_name.lower()
    uid = members["by_name"][name]["user_id"]
    return "[{name}](#narrow/pm-with/{uid}-{first_name})".format(
        name=name, uid=uid, first_name=first_name
    )


def get_stream_messages(stream):
    request = {
        "anchor": 10000000000000000,
        "num_before": 5000,
        "num_after": 0,
        "narrow": json.dumps([{"operator": "stream", "operand": stream}]),
    }
    try:
        log.debug("Fetching Zulip messages")
        response = requests.get(MESSAGES_URL, params=request, auth=(ZULIP_EMAIL, ZULIP_KEY))
        messages = response.json()["messages"]
    except Exception as e:
        log.error("Could not fetch Zulip messages: %s", e)
        messages = []

    return messages


def guess_zulip_emails(users, members):
    """Get zulip emails for users

    Some users may not have the same email ids on zulip and recurse.com, in
    which case sending private messages will fail. This function tries to
    detect the zulip email based on the full name of the user.

    *NOTE*: The email in our DB is not changed. The email is temporarily set as
     an attribute on the user, so that notifications can be sent to the user.

    """
    EMAILS = members["by_email"]
    NAMES = members["by_name"]
    for user in users:
        if user.email not in EMAILS and user.get_full_name() in NAMES:
            user.zulip_email = NAMES[user.get_full_name()]
        else:
            # Either the email is correct OR
            # Both name and email have changed or account deleted!
            pass
    return users


def notify_uncrawlable_blogs(user, blogs, admins, debug=True):
    """Notify blog owner about blogs that are failing crawls."""
    subject = "Blaggregator: Action required!"
    context = dict(
        user=user,
        blogs=blogs,
        base_url=settings.ROOT_URL.rstrip("/"),
        admins=admins,
    )
    content = get_template("home/disabling-crawling.md").render(context)
    to = getattr(user, "zulip_email", user.email)
    type_ = "private"
    if debug:
        log.debug("Sending message \n\n%s\n\n to %s (%s)", content, to, type_)
        return False

    else:
        return send_message_zulip(to, subject, content, type_=type_)


def send_message_zulip(to, subject, content, type_="private"):
    """Send a message to Zulip."""
    data = {"type": type_, "to": to, "subject": subject, "content": content}
    try:
        log.debug('Sending message "%s" to %s (%s)', content, to, type_)
        response = requests.post(MESSAGES_URL, data=data, auth=(ZULIP_EMAIL, ZULIP_KEY))
        log.debug(
            "Post returned with %s: %s",
            response.status_code,
            response.content,
        )
        return response.status_code == 200

    except Exception as e:
        log.exception(e)
        return False


def strip_batch(name):
    """Strip parenthesized batch from a name"""
    return re.sub(r"\(.*\)", "", name).strip()
