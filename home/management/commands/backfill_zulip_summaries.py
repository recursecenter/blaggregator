# Standard library
import logging
import re
from textwrap import indent
import time

# 3rd-party library
from django.core.management.base import BaseCommand

# Local library
from home.models import STREAM_CHOICES, Post
from home.zulip_helpers import (
    ZULIP_EMAIL,
    create_summary,
    get_stream_messages,
    update_message_content,
)

log = logging.getLogger("blaggregator")
# The link to the post, in the announcements we send
POST_URL = re.compile(r"/post/(\w+)/view")
# Announcements with a summary already have a quote block
QUOTE_BLOCK = re.compile(r"^`{3,}quote$", re.MULTILINE)


class Command(BaseCommand):
    help = (
        "Add summaries to the Zulip announcements of posts that don't have one. "
        "Only shows what it would do, unless --apply is passed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--stream",
            dest="streams",
            action="append",
            help="A stream to update announcements in. Can be repeated. "
            "Default: the streams blogs are announced in.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=1000,
            help="The number of latest announcements to look at, in each stream.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.3,
            help="Seconds to wait between edits, to stay within the rate limits.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Edit the messages on Zulip, instead of just showing what would change.",
        )

    def handle(self, **options):
        streams = options["streams"] or [name for _, name in STREAM_CHOICES]
        for stream in streams:
            self.stdout.write(f"Stream: {stream}")
            counts = backfill_summaries(
                stream,
                options["limit"],
                apply=options["apply"],
                delay=options["delay"],
                write=self.stdout.write,
            )
            summary = ", ".join(f"{count} {name}" for name, count in counts.items())
            self.stdout.write(summary)
        if not options["apply"]:
            self.stdout.write("This was a dry run. Pass --apply to edit the messages.")


def preview(content, length=100):
    """The start of the message, on one line."""
    text = " ".join(content.split())
    return text if len(text) <= length else text[: length - 3] + "..."


def backfill_summaries(stream, limit, apply=False, delay=0.0, write=print):
    """Add the summary of the post to the announcements that don't have one.

    Return a count of what was done with the messages we looked at.

    """
    counts = {
        "updated" if apply else "to update": 0,
        "failed": 0,
        "already have a summary": 0,
        "have no summary": 0,
        "have no link to a post": 0,
        "link to unknown posts": 0,
    }
    updated = "updated" if apply else "to update"
    messages = get_stream_messages(stream, sender=ZULIP_EMAIL, raw=True, limit=limit)
    slugs = {m["id"]: POST_URL.search(m["content"]) for m in messages}
    posts = Post.objects.filter(
        slug__in=[match.group(1) for match in slugs.values() if match]
    )
    posts = {post.slug: post for post in posts}

    for message in messages:
        content = message["content"]
        match = slugs[message["id"]]
        post = posts.get(match.group(1)) if match else None
        if match is None:
            counts["have no link to a post"] += 1
            write(f"Skipping message {message['id']}, no link to a post: {preview(content)}")
        elif post is None:
            counts["link to unknown posts"] += 1
            write(
                f"Skipping message {message['id']}, unknown post {match.group(1)}: "
                f"{preview(content)}"
            )
        elif QUOTE_BLOCK.search(content):
            counts["already have a summary"] += 1
        elif not (summary := create_summary(post.content) if post.content else ""):
            counts["have no summary"] += 1
        elif not apply:
            write(f"Would update message {message['id']}: {post.title}")
            write(indent(content + summary, "    | ", lambda line: True))
            write("")
            counts[updated] += 1
        elif update_message_content(message["id"], content + summary):
            write(f"Updated message {message['id']}: {post.title}")
            counts[updated] += 1
            time.sleep(delay)
        else:
            write(f"Could not update message {message['id']}: {post.title}")
            counts["failed"] += 1
    return counts
