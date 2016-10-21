from django.utils import timezone
import factory

from home.models import Blog, Post, User

tzinfo = timezone.get_default_timezone()


def create_posts(n):
    """Create the specified number of posts."""
    return PostFactory.create_batch(n)


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('ssn')


class BlogFactory(factory.DjangoModelFactory):
    class Meta:
        model = Blog

    user = factory.SubFactory(UserFactory)


# FIXME: hypothesis doesn't work with this version of Django, if not we
# probably wouldn't need all these factories!!
class PostFactory(factory.DjangoModelFactory):
    class Meta:
        model = Post

    url = factory.Faker('uri')
    date_posted_or_crawled = factory.Faker('date_time_this_decade', after_now=True, tzinfo=tzinfo)
    title = factory.Faker('sentence')
    content = factory.Faker('text')
    blog = factory.SubFactory(BlogFactory)
