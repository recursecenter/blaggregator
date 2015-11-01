from django.contrib.syndication.views import Feed

from home.models import Post

class LatestEntriesFeed(Feed):
    title = "Blaggregator"
    link = "/feed/"
    description = "Syndicated feed for blaggregator."
    description_template = 'home/feed_item.tmpl'

    def items(self):
        return Post.objects.order_by('-date_updated')[:100]

    def item_title(self, post):
        return post.title

    def item_description(self, post):
        return post.content

    def item_link(self, post):
        return post.url

    def item_author_name(self, post):
        user = post.blog.user
        return user.first_name + " " + user.last_name

    def item_pubdate(self, post):
        return post.date_updated
