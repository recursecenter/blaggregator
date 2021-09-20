"""Utilities for tests."""
from django.utils import feedgenerator, timezone
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from mock import Mock

from home.models import Blog, Post, User

tzinfo = timezone.get_default_timezone()
alphabet = "".join([chr(i) for i in range(32, 2 ** 10)])

fake = Faker(["it_IT", "en_US", "ja_JP"])


def _generate_feed(atom=False):
    link = fake.url()
    feed = {
        "title": fake.sentence(),
        "link": link,
        "description": fake.sentence(),
    }
    optional = {
        "language": fake.locale(),
        "author_email": fake.email(),
        "author_name": fake.name(),
        "author_link": fake.url(),
        "subtitle": fake.sentence(),
        "categories": fake.pylist(nb_elements=5, value_types=[fake.word]),
        "feed_url": fake.url(),
        "feed_copyright": fake.sentence(),
        "id": link if atom else fake.uuid4(),
        "ttl": fake.pyint(),
    }
    feed.update([(k, v) for (k, v) in optional.items() if fake.pybool()])
    return feed


def _generate_item(atom=False):
    link = fake.url()
    item = {
        "title": fake.sentence(),
        "link": link,
        "description": fake.sentence(),
    }
    optional = {
        "content": fake.paragraph(),
        "author_email": fake.email(),
        "author_name": fake.name(),
        "author_link": fake.url(),
        "pubdate": fake.date_time(),
        "updateddate": fake.date_time(),
        "unique_id": link if atom else fake.uuid4(),
        "categories": fake.pylist(nb_elements=5, value_types=[fake.word]),
        "item_copyright": fake.sentence(),
        "ttl": fake.pyint(),
    }
    item.update([(k, v) for (k, v) in optional.items() if fake.pybool()])
    return item


def generate_full_feed(min_items=0, max_items=20):
    atom = fake.boolean()
    generator = feedgenerator.Atom1Feed if atom else feedgenerator.Rss201rev2Feed
    feed = generator(**_generate_feed(atom=atom))
    items = [
        _generate_item(atom=atom)
        for _ in range(fake.pyint(min_value=min_items, max_value=max_items))
    ]
    for item in items:
        feed.add_item(**item)

    return feed


def create_posts(n, **kwargs):
    """Create the specified number of posts."""
    return PostFactory.create_batch(n, **kwargs)


def fake_response(text):
    def wrapped(*args, **kwargs):
        response = Mock()
        response.headers = {}
        response.read = Mock(return_value=text.strip())
        response.url = ""
        return response

    return wrapped


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class BlogFactory(DjangoModelFactory):
    class Meta:
        model = Blog

    user = factory.SubFactory(UserFactory)
    feed_url = factory.Faker("uri")


class PostFactory(DjangoModelFactory):
    class Meta:
        model = Post

    url = factory.Faker("uri")
    posted_at = factory.Faker("date_time_this_decade", after_now=True, tzinfo=tzinfo)
    title = factory.Faker("sentence")
    content = factory.Faker("text")
    blog = factory.SubFactory(BlogFactory)
