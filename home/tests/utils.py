"""Utilities for tests."""
from django.utils import timezone
import factory
import feedgenerator
from hypothesis import strategies as st
from hypothesis.extra.datetime import datetimes
from hypothesis.extra.fakefactory import fake_factory

from home.models import Blog, Post, User

tzinfo = timezone.get_default_timezone()
alphabet = ''.join([unichr(i) for i in range(32, 2 ** 10)])


def _valid_text(allow_empty=True):
    return st.text(alphabet).map(
        lambda x: ('.' if not allow_empty else '') + x
    )


def _optional(s):
    return st.one_of(s, st.none())


def _generate_feed(atom=False):
    feed = {
        'title': _valid_text(),
        'link': fake_factory('url'),
        'description': _valid_text(),
    }
    optional = {
        'language': fake_factory('locale').map(lambda x: x.replace('_', '-')),
        'author_email': fake_factory('email'),
        'author_name': fake_factory('name'),
        'author_link': fake_factory('url'),
        'subtitle': _valid_text(),
        'categories': st.lists(_valid_text()),
        'feed_url': fake_factory('url'),
        'feed_copyright': _valid_text(),
        'id': fake_factory('url') if atom else _valid_text(),
        'ttl': st.integers(min_value=0),
    }
    feed.update([(k, _optional(v)) for (k, v) in optional.items()])
    return feed


def _generate_item(atom=False):
    link = fake_factory('url')
    item = {
        'title': _valid_text(allow_empty=False),
        'link': link,
        'description': _valid_text(),
    }
    optional = {
        'content': _valid_text(),
        'author_email': fake_factory('email'),
        'author_name': fake_factory('name'),
        'author_link': fake_factory('url'),
        'pubdate': datetimes(),
        'updateddate': datetimes(),
        # 'comments': to_unicode(comments),
        'unique_id': link if atom else _valid_text(),
        # # 'enclosure': enclosure,
        # # 'categories': st.lists(_valid_text()),
        'item_copyright': _valid_text(),
        'ttl': st.integers(min_value=0),
    }
    item.update([(k, _optional(v)) for (k, v) in optional.items()])
    return item


def create_posts(n, **kwargs):
    """Create the specified number of posts."""
    return PostFactory.create_batch(n, **kwargs)


def generate_feed():
    rss = st.builds(feedgenerator.Rss201rev2Feed, ** _generate_feed())
    atom = st.builds(feedgenerator.Atom1Feed, ** _generate_feed(atom=True))
    return st.one_of(rss, atom)


def generate_full_feed(min_items=0, max_items=20):

    def _create_feed(feed, items):
        for item in items:
            feed.add_item(**item)
        return feed

    return st.builds(
        _create_feed,
        generate_feed(),
        generate_items(min_size=min_items, max_size=max_items),
    )


def generate_items(min_size=0, max_size=20):
    return st.lists(
        st.builds(dict, ** _generate_item()),
        min_size=min_size,
        max_size=max_size
    )


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = User

    username = factory.Faker('ssn')


class BlogFactory(factory.DjangoModelFactory):

    class Meta:
        model = Blog

    user = factory.SubFactory(UserFactory)
    feed_url = factory.Faker('uri')


# FIXME: hypothesis doesn't work with this version of Django, if not we
# probably wouldn't need all these factories!!
class PostFactory(factory.DjangoModelFactory):

    class Meta:
        model = Post

    url = factory.Faker('uri')
    posted_at = factory.Faker(
        'date_time_this_decade', after_now=True, tzinfo=tzinfo
    )
    title = factory.Faker('sentence')
    content = factory.Faker('text')
    blog = factory.SubFactory(BlogFactory)
