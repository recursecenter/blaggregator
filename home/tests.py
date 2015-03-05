"""Blaggregator Tests."""

from unittest import expectedFailure

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

from home.oauth import create_user, HackerSchoolOAuth2, create_or_update_hacker


class BlaggregatorNoLoginTests(TestCase):

    def test_shows_about_without_login(self):
        # Given
        client = self.client

        # When
        response = client.get('/about/')

        # Then
        self.assertEqual(200, response.status_code)

    @expectedFailure
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
        self.assertIn('Login with Hacker School', response.content)

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
        self.assertRedirectPath(response, 'new')

    def test_logout_redirects_to_home(self):
        # Given
        client = self.client

        # When
        response = client.get('/logout/')

        # Then
        self.assertRedirectPath(response, '/')

    # Assertions ####

    def assertRedirectPath(self, response, path, redirect=302):
        self.assertEqual(redirect, response.status_code)
        actual_path = response.get('Location', '').rsplit('/', 1)[-1]
        self.assertEqual(path.strip('/'), actual_path)
