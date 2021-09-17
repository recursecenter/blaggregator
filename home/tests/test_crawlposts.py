from io import BytesIO

from django.core.management import execute_from_command_line
from django.conf import settings
from django.test import TransactionTestCase
from mock import patch

from home.models import Blog, Post, User
from .utils import BlogFactory, generate_full_feed


def random_feed(url=None, data=None, timeout=None):
    feed = generate_full_feed(min_items=5, max_items=20).example()
    xml = feed.writeString("utf8")
    return BytesIO(xml.encode("utf8"))


@patch("home.zulip_helpers.update_user_details", new=lambda x: None)
@patch("home.zulip_helpers.get_members", new=lambda: {"by_id": {}})
@patch("urllib.request.OpenerDirector.open", new=random_feed)
@patch("requests.post")
class CrawlPostsTestCase(TransactionTestCase):
    def setUp(self):
        # Setup the db with blogs
        BlogFactory.create_batch(2)
        self.blogs = Blog.objects.all()
        super(CrawlPostsTestCase, self).setUp()

    def tearDown(self):
        self.clear_db()
        super(CrawlPostsTestCase, self).tearDown()

    def clear_db(self):
        User.objects.all().delete()

    def test_crawling_posts(self, mock):
        # When
        execute_from_command_line(["./manage.py", "crawlposts"])
        # Then
        for blog in self.blogs:
            # at least one post per blog
            self.assertGreater(Post.objects.filter(blog=blog).count(), 0)
            # posts are unique by blog and title
            post_titles = Post.objects.filter(blog=blog).values_list("title", flat=True)
            self.assertEqual(len(set(post_titles)), len(post_titles))
        # Number of announcements are correctly throttled
        self.assertLessEqual(
            mock.call_count, settings.MAX_POST_ANNOUNCE * self.blogs.count()
        )

    def test_crawling_skips_flagged_blogs(self, mock):
        # Given
        blog1, blog2 = list(self.blogs)
        blog1.skip_crawl = True
        blog1.save()
        # When
        execute_from_command_line(["./manage.py", "crawlposts"])
        # Then
        self.assertEqual(0, Post.objects.filter(blog=blog1).count())
        self.assertLess(0, Post.objects.filter(blog=blog2).count())
