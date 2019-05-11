# Standard library
import logging
import re

# 3rd-party library
from django.core.management.base import BaseCommand

# Local library
from home.models import Post
from home.utils import is_medium_comment
from home.zulip_helpers import delete_message, get_stream_messages

log = logging.getLogger("blaggregator")
EMAIL_PREFIX = "blaggregator-bot@"


class Command(BaseCommand):
    help = "Delete all medium comments and zulip announcements for them."

    def add_arguments(self, parser):
        parser.add_argument(
            "--stream",
            dest="stream",
            type=str,
            default="blogging",
            help="The stream to clean-up Zulip announcements from.",
        )

    def handle(self, **options):
        slugs = [
            post.slug
            for post in Post.objects.filter(url__icontains="medium.com")
            if is_medium_comment(post)
        ]
        delete_messages_with_slugs(slugs, options["stream"])
        Post.objects.filter(slug__in=slugs).delete()


def delete_messages_with_slugs(slugs, stream):
    messages = get_stream_messages(stream)
    bot_messages = [
        message
        for message in messages
        if message["sender_email"].startswith(EMAIL_PREFIX)
    ]
    slug_re = re.compile("/post/({})/view".format("|".join(slugs)))
    for message in bot_messages:
        if slug_re.search(message["content"]):
            delete_message(message["id"], "(medium comment deleted)")
