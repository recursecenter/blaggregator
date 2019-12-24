import json

from django.test import TestCase
from mock import patch
from requests import Response

from home.models import User
from home.oauth import HackerSchoolOAuth2, update_user_details


def request(self, url, method='GET', *args, **kwargs):
    if url.endswith('/oauth/token'):
        data = {
            'access_token': 'x',
            'created_at': 1478432443,
            'expires_in': 7200,
            'token_type': 'bearer',
            'scope': 'public',
            'refresh_token': 'y'
        }
    else:
        data = OAuthTestCase.USER_DATA

    response = Response()
    response._content = json.dumps(data).encode("utf8")
    response.status_code = 200
    return response


@patch('home.oauth.HackerSchoolOAuth2.validate_state', new=lambda x: True)
@patch('home.oauth.HackerSchoolOAuth2.request', new=request)
class OAuthTestCase(TestCase):

    USER_DATA = {
        'id': 1729,
        'email': 'johndoe@foo-bar.com',
        'image': 'https://x.cloudfront.net/assets/people/y.jpg',
        'first_name': 'John',
        'last_name': 'Doe',
        'github': 'johndoe',
    }

    def setUp(self):
        pass

    def tearDown(self):
        self.clear_db()

    def clear_db(self):
        User.objects.all().delete()

    def test_login_redirects_to_authorization_url(self):
        # When
        response = self.client.get('/login/hackerschool/')

        # Then
        self.assertEqual(302, response.status_code)
        self.assertTrue(response['Location'].startswith(HackerSchoolOAuth2.AUTHORIZATION_URL))

    def test_authorization_completes(self):
        # When
        response = self.client.get('/complete/hackerschool/')

        # Then
        self.assertEqual(302, response.status_code)
        self.assertTrue(response['Location'].endswith('/new/'))
        self.assertEqual(1, User.objects.count())
        user = User.objects.get(email=self.USER_DATA['email'])
        self.assertEqual(user.hacker.avatar_url, self.USER_DATA['image'])
        self.assertEqual(user.hacker.github, self.USER_DATA.get('github', ''))
        self.assertEqual(user.hacker.twitter, self.USER_DATA.get('twitter', ''))

    def test_authenticates_existing_user(self):
        # When
        self.client.get('/complete/hackerschool/')
        self.client.get('/logout/', follow=True)
        response = self.client.get('/complete/hackerschool/')

        # Then
        self.assertEqual(302, response.status_code)
        self.assertTrue(response['Location'].endswith('/new/'))
        self.assertEqual(1, User.objects.count())
        user = User.objects.get(email=self.USER_DATA['email'])
        self.assertEqual(user.hacker.avatar_url, self.USER_DATA['image'])
        self.assertEqual(user.hacker.github, self.USER_DATA.get('github', ''))
        self.assertEqual(user.hacker.twitter, self.USER_DATA.get('twitter', ''))

    def test_updates_user_details(self):
        # When
        self.client.get('/complete/hackerschool/')
        user = User.objects.get(email=self.USER_DATA['email'])
        self.USER_DATA['twitter'] = 'johndoe'

        # When
        with patch('requests.get', new=lambda url: request(None, url)):
            update_user_details(self.USER_DATA['id'])

        # Then
        user = User.objects.get(email=self.USER_DATA['email'])
        self.assertEqual(user.hacker.twitter, 'johndoe')
