"""Blaggregator Tests."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from home.models import Blog


class BlaggregatorNoLoginTests(TestCase):

    def test_shows_about_without_login(self):
        # Given
        client = self.client

        # When
        response = client.get('/about/')

        # Then
        self.assertEqual(200, response.status_code)

    def test_404_for_unknown_slug(self):
        # Given
        client = self.client

        # When
        response = client.get('/post/BOGUS/view')

        # Then
        self.assertEqual(404, response.status_code)

    def test_should_prompt_login(self):
        # Given
        client = self.client

        # When
        response = client.get('/login/')

        # Then
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Login with Hacker School')

@override_settings(
    AUTHENTICATION_BACKENDS=(
        'django.contrib.auth.backends.ModelBackend',
    ),
)
class BlaggregatorLoggedInTests(TestCase):

    @classmethod
    def setUpClass(cls):
        User.objects.create_user('test_user')
        test_user = User.objects.get(username='test_user')
        test_user.set_password('test_user')
        test_user.save()

    def setUp(self):
        self.client.login(username='test_user', password='test_user')

    # Tests ####

    def test_should_redirect_logged_in_user_to_new(self):
        # Given
        client = self.client

        # When
        response = client.get('/login/')

        # Then
        self.assertRedirects(response, '/new', target_status_code=301)

    def test_logout_redirects_to_home(self):
        # Given
        client = self.client

        # When
        response = client.get('/logout/')

        # Then
        self.assertRedirects(response, '/', target_status_code=302)

    def test_should_show_add_blog_form(self):
        # Given
        client = self.client

        # When
        response = client.get('/add_blog/')

        # Then
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Add Your Blog')

    def test_should_error_when_no_feed_url(self):
        # Given
        client = self.client

        # When
        response = client.post('/add_blog/')

        # Then
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'go back and try again')

    def test_should_add_blog(self):
        # Given
        client = self.client
        feed_url = 'https://www.hackerschool.com/blog.rss'

        # When
        response = client.post('/add_blog/', data={'feed_url': feed_url})

        # Then
        self.assertRedirects(response, '/new', target_status_code=301)
        self.assertIsNotNone(Blog.objects.get(feed_url=feed_url))

    def test_should_delete_blog(self):
        # Given
        client = self.client
        feed_url = 'https://www.hackerschool.com/blog.rss'
        client.post('/add_blog/', data={'feed_url': feed_url})
        blog = Blog.objects.get(feed_url=feed_url)

        # When
        client.get('/delete_blog/%s/' % blog.id)

        # Then
        with self.assertRaises(Blog.DoesNotExist):
            Blog.objects.get(feed_url=feed_url)
