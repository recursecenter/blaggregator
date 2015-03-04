"""Blaggregator Tests."""

from unittest import expectedFailure

from django.test import TestCase
from django.test.client import Client


class BlaggregatorNoLoginTests(TestCase):

    def test_shows_about_without_login(self):
        # Given
        client = Client()

        # When
        response = client.get('/about/')

        # Then
        self.assertEqual(200, response.status_code)

    @expectedFailure
    def test_404_for_unknown_slug(self):
        # Given
        client = Client()

        # When
        response = client.get('/post/BOGUS/view')

        # Then
        self.assertEqual(404, response.status_code)

    def test_should_prompt_login(self):
        # Given
        client = Client()

        # When
        response = client.get('/login/')

        # Then
        self.assertEqual(200, response.status_code)
        self.assertIn('Log in with Hacker School', response.content)
