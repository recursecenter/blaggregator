from django.conf import settings
from django.contrib.syndication.views import Feed
from django.utils import feedgenerator

from home.models import Post


class LatestEntriesFeed(Feed):
    feed_type = feedgenerator.Atom1Feed
    title = "Blaggregator"
    link = "/atom.xml"
    description = "Syndicated feed for blaggregator."
    description_template = 'home/feed_item.tmpl'

    def items(self):
        return Post.objects.all()[:settings.MAX_FEED_ENTRIES]

    def item_title(self, item):
        return item.title

    def item_link(self, item):
        return item.url

    def item_author_name(self, item):
        user = item.blog.user
        return user.first_name + " " + user.last_name

    def item_pubdate(self, item):
        return item.posted_at
