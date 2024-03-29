from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
import feedparser
from mock import patch

from home.models import Hacker, Blog, LogEntry, Post, User
from .utils import create_posts, fake_response

N_MAX = settings.MAX_FEED_ENTRIES


@override_settings(
    AUTHENTICATION_BACKENDS=(
        "django.contrib.auth.backends.ModelBackend",
        "home.token_auth.TokenAuthBackend",
    )
)
class BaseViewTestCase(TestCase):
    def setUp(self):
        self.setup_test_user()

    def tearDown(self):
        self.clear_db()

    # Helper methods ####
    def clear_db(self):
        User.objects.all().delete()

    def create_posts(self, n, **kwargs):
        create_posts(n, **kwargs)
        # Blog.objects.update(user=self.user)

    def setup_test_user(self):
        self.username = self.password = "test"
        self.user = User.objects.create_user(self.username)
        self.user.set_password(self.password)
        self.user.save()
        self.hacker = Hacker.objects.create(user_id=self.user.id)

    def login(self):
        """Login as test user."""
        self.client.login(username=self.username, password=self.password)


class FeedsViewTestCase(BaseViewTestCase):
    def test_should_enforce_authentication(self):
        response = self.client.get("/atom.xml")
        self.assertEqual(response.status_code, 403)
        response = self.client.get("/atom.xml", data={"token": ""})
        self.assertEqual(response.status_code, 403)

    def test_should_enforce_token(self):
        self.login()
        response = self.client.get("/new/")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/atom.xml")
        self.assertEqual(response.status_code, 403)
        response = self.client.get("/atom.xml", data={"token": ""})
        self.assertEqual(response.status_code, 403)
        response = self.client.get("/atom.xml", data={"token": "BOGUS-TOKEN"})
        self.assertEqual(response.status_code, 403)

    def test_feed_with_no_posts(self):
        self.verify_feed_generation(0)

    def test_feed_with_posts_less_than_max_feed_size(self):
        self.verify_feed_generation(N_MAX - 1)

    def test_feed_with_posts_more_than_max_feed_size(self):
        self.verify_feed_generation(N_MAX * 5)

    def test_feed_with_control_characters(self):
        # Given
        blog = Blog.objects.create(user=self.user)
        Post.objects.create(
            blog=blog,
            title="This is a title with control chars \x01",
            content="This is content with control chars \x01",
            posted_at=timezone.now(),
        )

        # When
        response = self.client.get("/atom.xml", data={"token": self.hacker.token})

        # Then
        self.assertEqual(1, Post.objects.count())
        text = response.content.decode("utf8")
        self.assertIn(
            "This is a title with control chars",
            text,
        )
        self.assertIn(
            "This is content with control chars",
            text,
        )

    # Helper methods ####
    def parse_feed(self, content):
        """Parse feed content and return entries."""
        # FIXME: Would it be a good idea to use feedergrabber?
        return feedparser.parse(content)

    def get_included_excluded_posts(self, posts, entries):
        """Returns the set of included and excluded posts."""
        entry_links = {(entry.title, entry.link) for entry in entries}
        included = []
        excluded = []
        for post in posts:
            if (post.title, post.url) in entry_links:
                included.append(post)
            else:
                excluded.append(post)
        return included, excluded

    def verify_feed_generation(self, n):
        # Given
        self.clear_db()
        self.login()
        self.setup_test_user()
        posts = create_posts(n)
        # When
        response = self.client.get("/atom.xml", data={"token": self.hacker.token})
        # Then
        self.assertEqual(n, Post.objects.count())
        self.assertEqual(n, len(posts))
        self.assertEqual(200, response.status_code)
        feed = self.parse_feed(response.content)
        entries = feed.entries
        self.assertEqual(min(n, N_MAX), len(entries))
        if n < 1:
            return

        self.assertGreaterEqual(entries[0].updated_parsed, entries[-1].updated_parsed)
        included, excluded = self.get_included_excluded_posts(posts, entries)
        self.assertEqual(len(included), len(entries))
        if not excluded:
            return

        max_excluded_date = max(excluded, key=lambda x: x.posted_at).posted_at
        min_included_date = min(included, key=lambda x: x.posted_at).posted_at
        self.assertGreaterEqual(min_included_date, max_excluded_date)


EMPTY_FEED = b"""
<?xml version="1.0" encoding="utf-8" standalone="yes" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>My Site</title>
    <link>http://localhost:1313/</link>
    <language>en-us</language>
    <atom:link href="http://localhost:1313/index.xml" rel="self" type="application/rss+xml" />
  </channel>
</rss>
"""
HTML_PAGE = b"""
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <title>My Site</title>
        <link href="/favicon.ico" rel="icon">
        <link href="/stylesheets/screen.css" media="screen, projection" rel="stylesheet" type="text/css">
        <link href="https://jvns.ca/atom.xml" rel="alternate" type="application/atom+xml">
    </head>
    <body>
    </body>
</html>
"""


html_page = fake_response(HTML_PAGE)
empty_feed = fake_response(EMPTY_FEED)


@patch("urllib.request.OpenerDirector.open", new=empty_feed)
class AddBlogViewTestCase(BaseViewTestCase):
    def test_get_add_blog_requires_login(self):
        # When
        response = self.client.post("/add_blog/", follow=True)
        # Then
        self.assertRedirects(response, "/login/?next=/add_blog/")

    def test_post_add_blog_without_blog_url_barfs(self):
        # Given
        self.login()
        # When
        response = self.client.post("/add_blog/", follow=True)
        # Then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No feed URL provided")

    def test_post_add_blog_adds_blog(self):
        # Given
        self.login()
        data = {"feed_url": "https://jvns.ca/atom.xml"}
        # When
        response = self.client.post("/add_blog/", data=data, follow=True)
        # Then
        self.assertRedirects(response, "/profile/{}/".format(self.user.id))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(Blog.objects.get(feed_url=data["feed_url"]))
        self.assertContains(response, "has been added successfully")

    def test_post_add_blog_adds_blog_without_schema(self):
        # Given
        self.login()
        data = {"feed_url": "jvns.ca/atom.xml"}
        # When
        response = self.client.post("/add_blog/", data=data, follow=True)
        # Then
        self.assertRedirects(response, "/profile/{}/".format(self.user.id))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(Blog.objects.get(feed_url="http://{}".format(data["feed_url"])))

    def test_post_add_blog_adds_only_once(self):
        # Given
        self.login()
        data = {"feed_url": "https://jvns.ca/atom.xml"}
        self.client.post("/add_blog/", data=data, follow=True)
        data_ = {"feed_url": "https://jvns.ca/atom.xml"}
        # When
        response = self.client.post("/add_blog/", data=data_, follow=True)
        # Then
        self.assertRedirects(response, "/profile/{}/".format(self.user.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, Blog.objects.count())

    def test_post_add_blog_existing_unsets_skip_crawl(self):
        # Given
        self.login()
        data = {"feed_url": "https://jvns.ca/atom.xml"}
        self.client.post("/add_blog/", data=data, follow=True)
        blog = Blog.objects.get(feed_url=data["feed_url"])
        blog.skip_crawl = True
        blog.save()
        data_ = {"feed_url": "https://jvns.ca/atom.xml"}
        # When
        response = self.client.post("/add_blog/", data=data_, follow=True)
        # Then
        self.assertRedirects(response, "/profile/{}/".format(self.user.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, Blog.objects.count())
        blog = Blog.objects.get(feed_url=data["feed_url"])
        self.assertFalse(blog.skip_crawl)

    def test_post_add_blog_adds_different_feeds(self):
        # Given
        self.login()
        data = {"feed_url": "https://jvns.ca/atom.xml"}
        self.client.post("/add_blog/", data=data, follow=True)
        data_ = {"feed_url": "https://jvns.ca/tags/blaggregator.xml"}
        # When
        response = self.client.post("/add_blog/", data=data_, follow=True)
        # Then
        self.assertRedirects(response, "/profile/{}/".format(self.user.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, Blog.objects.count())
        self.assertIsNotNone(Blog.objects.get(feed_url=data["feed_url"]))

    def test_post_add_blog_suggests_feed_url(self):
        # Given
        self.login()
        data = {"feed_url": "https://jvns.ca/"}
        # When
        with patch("urllib.request.OpenerDirector.open", new=html_page):
            response = self.client.post("/add_blog/", data=data, follow=True)
        # Then
        self.assertEqual(0, Blog.objects.count())
        self.assertRedirects(response, "/profile/{}/".format(self.user.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please use your blog's feed url")
        self.assertContains(response, "It could be -- ")
        self.assertContains(response, "https://jvns.ca/atom.xml")


class DeleteBlogViewTestCase(BaseViewTestCase):
    def test_should_not_delete_blog_not_logged_in(self):
        # Given
        feed_url = "https://jvns.ca/atom.xml"
        blog = Blog.objects.create(user=self.user, feed_url=feed_url)
        # When
        self.client.get("/delete_blog/%s/" % blog.id)
        # Then
        self.assertEqual(1, Blog.objects.count())

    def test_should_delete_blog(self):
        # Given
        self.login()
        feed_url = "https://jvns.ca/atom.xml"
        blog = Blog.objects.create(user=self.user, feed_url=feed_url)
        # When
        self.client.get("/delete_blog/%s/" % blog.id)
        # Then
        self.assertEqual(0, Blog.objects.count())
        with self.assertRaises(Blog.DoesNotExist):
            Blog.objects.get(feed_url=feed_url)

    def test_should_not_delete_unknown_blog(self):
        # Given
        self.login()
        feed_url = "https://jvns.ca/atom.xml"
        blog = Blog.objects.create(user=self.user, feed_url=feed_url)
        self.client.get("/delete_blog/%s/" % blog.id)
        # When
        response = self.client.get("/delete_blog/%s/" % blog.id)
        # Then
        self.assertEqual(404, response.status_code)


class EditBlogViewTestCase(BaseViewTestCase):
    def test_should_not_edit_blog_not_logged_in(self):
        # Given
        feed_url = "https://jvns.ca/atom.xml"
        blog = Blog.objects.create(user=self.user, feed_url=feed_url)
        # When
        response = self.client.get("/edit_blog/%s/" % blog.id, follow=True)
        # Then
        self.assertRedirects(response, "/login/?next=/edit_blog/%s/" % blog.id)

    def test_should_edit_blog(self):
        # Given
        self.login()
        feed_url = "https://jvns.ca/atom.xml"
        blog = Blog.objects.create(user=self.user, feed_url=feed_url)
        data = {"feed_url": "https://jvns.ca/rss", "stream": "BLOGGING"}
        # When
        response = self.client.post("/edit_blog/%s/" % blog.id, data=data, follow=True)
        # Then
        self.assertEqual(200, response.status_code)
        with self.assertRaises(Blog.DoesNotExist):
            Blog.objects.get(feed_url=feed_url)
        self.assertIsNotNone(Blog.objects.get(feed_url=data["feed_url"]))

    def test_should_unset_skip_crawl_on_edit_blog(self):
        # Given
        self.login()
        feed_url = "https://jvns.ca/atom.xml"
        blog = Blog.objects.create(user=self.user, feed_url=feed_url, skip_crawl=True)
        data = {"feed_url": "https://jvns.ca/rss", "stream": "BLOGGING"}
        assert blog.skip_crawl, "Blog skip crawl should be True"
        # When
        response = self.client.post("/edit_blog/%s/" % blog.id, data=data, follow=True)
        # Then
        self.assertEqual(200, response.status_code)
        with self.assertRaises(Blog.DoesNotExist):
            Blog.objects.get(feed_url=feed_url)
        blog = Blog.objects.get(feed_url=data["feed_url"])
        self.assertIsNotNone(blog)
        self.assertFalse(blog.skip_crawl)

    def test_should_not_edit_unknown_blog(self):
        # Given
        self.login()
        data = {"feed_url": "https://jvns.ca/rss", "stream": "BLOGGING"}
        # When
        response = self.client.post("/edit_blog/%s/" % 200, data=data, follow=True)
        # Then
        self.assertEqual(404, response.status_code)


class UpdatedAvatarViewTestCase(BaseViewTestCase):
    def test_should_update_avatar_url(self):
        # Given
        self.login()
        expected_url = "foo.bar"

        def update_user_details(user_id):
            self.user.hacker.avatar_url = expected_url
            self.user.hacker.save()

        # When
        with patch("home.views.update_user_details", new=update_user_details):
            response = self.client.get("/updated_avatar/%s/" % self.user.id, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(expected_url, response.content.decode("utf8"))

    def test_should_not_update_unknown_hacker_avatar_url(self):
        # Given
        self.login()
        # When
        with patch("home.views.update_user_details", new=lambda x, y: None):
            response = self.client.get("/updated_avatar/200/", follow=True)
        self.assertEqual(404, response.status_code)


class ViewPostViewTestCase(BaseViewTestCase):
    def test_should_redirect_to_post(self):
        # Given
        self.create_posts(1)
        post = Post.objects.filter()[0]
        post_url = post.url
        # When
        response = self.client.get("/post/{}/view/".format(post.slug))
        # Then
        self.assertEqual(response["Location"], post_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(1, LogEntry.objects.filter(post=post).count())

    def test_does_not_redirect_to_bogus_post(self):
        # When
        response = self.client.get("/post/BOGUS/view/")
        # Then
        self.assertEqual(response.status_code, 404)


class MostViewedViewTestCase(BaseViewTestCase):
    def test_should_enforce_authentication(self):
        # When
        response = self.client.get("/most_viewed/", follow=True)
        # Then
        self.assertRedirects(response, "/login/?next=/most_viewed/")

    def test_should_show_most_viewed_posts(self):
        # Given
        self.login()
        self.create_posts(10)
        post = Post.objects.filter()[0]
        self.client.get("/post/{}/view/".format(post.slug))
        # When
        response = self.client.get("/most_viewed/", follow=True)
        # Then
        self.assertContains(response, post.title)

    def test_should_show_most_viewed_posts_n_days(self):
        # Given
        self.login()
        self.create_posts(10)
        post = Post.objects.filter()[0]
        self.client.get("/post/{}/view/".format(post.slug))
        # When
        response = self.client.get("/most_viewed/30/", follow=True)
        # Then
        self.assertContains(response, post.title)

    def test_should_show_most_viewed_posts_tsv(self):
        # Given
        self.login()
        self.create_posts(10)
        post = Post.objects.filter()[0]
        self.client.get("/post/{}/view/".format(post.slug))
        # When
        response = self.client.get("/most_viewed/?tsv=1", follow=True)
        # Then
        self.assertEqual(response["Content-Type"], "text/tab-separated-values")
        self.assertContains(response, post.title)

    def test_should_show_most_viewed_posts_tsv_n_days(self):
        # Given
        self.login()
        self.create_posts(10)
        post = Post.objects.filter()[0]
        self.client.get("/post/{}/view/".format(post.slug))
        # When
        response = self.client.get("/most_viewed/30/?tsv=1", follow=True)
        # Then
        self.assertEqual(response["Content-Type"], "text/tab-separated-values")
        self.assertContains(response, post.title)


class NewViewTestCase(BaseViewTestCase):
    def test_should_show_new_posts(self):
        # Given
        self.login()
        self.create_posts(5)
        # When
        response = self.client.get("/new/", follow=True)
        # Then
        for post in Post.objects.all():
            self.assertContains(response, post.title)
            self.assertContains(response, post.slug)

    def test_should_paginate_new_posts(self):
        # Given
        self.login()
        self.create_posts(35)
        # When
        response_1 = self.client.get("/new/", follow=True)
        response_2 = self.client.get("/new/?page=2", follow=True)
        # Then
        for post in Post.objects.all():
            if post.title in response_1.content.decode("utf8"):
                self.assertContains(response_1, post.slug)
                self.assertNotContains(response_2, post.title)
            else:
                self.assertContains(response_2, post.title)
                self.assertContains(response_2, post.slug)


class SearchViewTestCase(BaseViewTestCase):
    def test_should_show_matching_posts(self):
        # Given
        self.login()
        query = "python"
        n = 5
        matching_title = "Python is awesome"
        non_matching_title = "Django rocks"
        self.create_posts(n, title=matching_title)
        self.create_posts(n, title=non_matching_title)
        # When
        response = self.client.get("/search/?q={}".format(query), follow=True)
        # Then
        for post in Post.objects.all():
            if post.title == matching_title:
                self.assertContains(response, post.title)
                self.assertContains(response, post.slug)
            else:
                self.assertNotContains(response, post.slug)
