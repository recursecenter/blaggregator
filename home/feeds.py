import re

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.utils import feedgenerator

from home.models import Post


# This code has been taken from
# https://salsa.debian.org/qa/distro-tracker/blob/d22c25f84c92cd34ce63f131f0f2fb604453dc16/distro_tracker/core/news_feed.py#L27
def filter_control_chars(method):
    # We have to filter out control chars otherwise the FeedGenerator
    # raises UnserializableContentError (see django/utils/xmlutils.py)
    def wrapped(self, obj):
        result = method(self, obj)
        return re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]", "", result)

    return wrapped


class LatestEntriesFeed(Feed):
    feed_type = feedgenerator.Atom1Feed
    title = "Blaggregator"
    link = "/atom.xml"
    description = "Syndicated feed for blaggregator."
    description_template = "home/feed_item.tmpl"

    def items(self):
        return Post.objects.all()[: settings.MAX_FEED_ENTRIES]

    @filter_control_chars
    def item_title(self, item):
        return item.title

    def item_link(self, item):
        return item.url

    def item_author_name(self, item):
        user = item.blog.user
        return user.first_name + " " + user.last_name

    def item_pubdate(self, item):
        return item.posted_at
