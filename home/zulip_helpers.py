# Standard library
import html
import json
import logging
import os
import re

# 3rd-party library
from bs4 import BeautifulSoup
from django.conf import settings
from django.template.loader import get_template
from django.urls import reverse
from markdownify import markdownify as md
import requests

from home.models import Hacker, Post
from home.oauth import update_user_details

ZULIP_KEY = os.environ.get("ZULIP_KEY")
ZULIP_EMAIL = os.environ.get("ZULIP_EMAIL")
MESSAGES_URL = "https://recurse.zulipchat.com/api/v1/messages"
MEMBERS_URL = "https://recurse.zulipchat.com/api/v1/users"
ANNOUNCE_MESSAGE = "{} has a new blog post: [{}]({})"
MIN_FENCE = 3
# Zulip mentions look like @**name**, @_**name** (silent) or @*group*
MENTION = re.compile(r"(?<!\\)@_?(\*{1,2})([^*\n]+)\1")
MENTION_START = re.compile(r"@(?=[*_])")
ZWSP = "\u200b"
ESCAPED_TAG = re.compile(r"&lt;/?[a-zA-Z]")
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
        if post.content:
            summary = create_summary(post.content)
            content = content + summary
        send_message_zulip(to, subject, content, type_="stream")


def sanitize_markdown(text):
    """Make markdown made from untrusted HTML safe to post inside a quote block.

    Zulip renders markdown inside quote blocks, so we remove anything that
    could notify people or break out of the block:

    - mentions (@**all**, @**name**, @_**name**, @*group*) are reduced to plain
      text. markdownify escapes literal asterisks, but '@<b>all</b>' becomes
      '@**all**', which would notify everyone.

    """
    text = MENTION.sub(r"@\2", text)
    return MENTION_START.sub("@" + ZWSP, text)


def quote(text):
    """Wrap text in a Zulip quote block.

    The fence is longer than any run of backticks in the text, so that code
    blocks or backticks in the text cannot close the quote block early.

    """
    longest = max((len(run) for run in re.findall("`+", text)), default=0)
    fence = "`" * max(MIN_FENCE, longest + 1)
    return f"\n{fence}quote\n{text}\n{fence}"


def create_summary(content, limit=480):
    """From the contents of the first paragraph with text (or the whole content if
    there is none),
    extract text up to a length of limit, preserving HTML tags.
    If nonempty, the returned value is a string formatted as markdown and surrounded by
    ```quote
    ```
    (the fence gets longer if the content has long runs of backticks)
    """
    # Some feeds escape their HTML twice (e.g., inside CDATA). But if there are
    # real tags, any "&lt;div&gt;" is text that talks about a tag; keep it.
    if "<" not in content and ESCAPED_TAG.search(content):
        content = html.unescape(content)
    soup = BeautifulSoup(content, "html.parser")
    # Skip paragraphs with no text, like the ones that only have an image
    summary = next((p for p in soup.find_all("p") if p.get_text().strip()), soup)
    if not summary.get_text().strip():
        return ""
    if len(summary.text) <= limit:
        return quote(sanitize_markdown(md(str(summary))))
    length = 0
    for string in summary.strings:
        if length >= limit:
            string.extract()
            continue
        if length + len(string) < limit:
            length = length + len(string)
            continue
        stopat = limit - length
        string.replace_with(string[:stopat], "...")
        length = limit
    return quote(sanitize_markdown(md(str(summary))))


def _edit_message(message_id, **fields):
    """Edit a message on Zulip. Return True if it worked."""
    message_url = "{}/{}".format(MESSAGES_URL, message_id)
    try:
        response = requests.patch(message_url, data=fields, auth=(ZULIP_EMAIL, ZULIP_KEY))
        result = response.json()
        assert result["result"] == "success", result.get("msg", result)
    except Exception as e:
        log.error("Could not edit Zulip message %s: %s", message_id, e)
        return False
    return True


def delete_message(message_id, content="(deleted)"):
    """Replace the content and topic of a message. Return True if it worked."""
    return _edit_message(message_id, content=content, subject=content)


def update_message_content(message_id, content):
    """Replace the content of a message. Return True if it worked."""
    return _edit_message(message_id, content=content)


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


def get_stream_messages(stream, sender=None, raw=False, limit=5000):
    """Return the latest messages (oldest first) in a stream.

    - sender: only return messages sent by this user (an email), like the ones
      we sent ourselves -- use ZULIP_EMAIL for that.
    - raw: return the markdown source of the messages in "content", instead of
      the rendered HTML.
    - limit: the maximum number of messages to return.

    """
    narrow = [{"operator": "stream", "operand": stream}]
    if sender:
        narrow.append({"operator": "sender", "operand": sender})
    request = {
        "anchor": "newest",
        "num_before": limit,
        "num_after": 0,
        "narrow": json.dumps(narrow),
        "apply_markdown": json.dumps(not raw),
    }
    try:
        log.debug("Fetching Zulip messages")
        response = requests.get(
            MESSAGES_URL, params=request, auth=(ZULIP_EMAIL, ZULIP_KEY)
        )
        data = response.json()
        assert data["result"] == "success", data.get("msg", data)
        messages = data["messages"]
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
