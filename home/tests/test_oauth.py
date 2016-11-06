import json

from django.test import TestCase
from mock import patch
from requests import Response

from home.models import User
from home.oauth import HackerSchoolOAuth2, update_user_details


def request(self, url, method='GET', *args, **kwargs):
    if url.endswith('/oauth/token'):
        data = {
            u'access_token': u'x',
            u'created_at': 1478432443,
            u'expires_in': 7200,
            u'token_type': u'bearer',
            u'scope': u'public',
            u'refresh_token': u'y'
        }
    else:
        data = OAuthTestCase.USER_DATA

    response = Response()
    response._content = json.dumps(data)
    return response


@patch('home.oauth.HackerSchoolOAuth2.validate_state', new=lambda x: True)
@patch('home.oauth.HackerSchoolOAuth2.request', new=request)
class OAuthTestCase(TestCase):

    USER_DATA = {
        u'id': 1729,
        u'email': u'johndoe@foo-bar.com',
        u'image': u'https://x.cloudfront.net/assets/people/y.jpg',
        u'first_name': u'John',
        u'last_name': u'Doe',
        u'github': u'johndoe',
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
        update_user_details(self.USER_DATA['id'], user)

        # Then
        user = User.objects.get(email=self.USER_DATA['email'])
        self.assertEqual(user.hacker.twitter, 'johndoe')
