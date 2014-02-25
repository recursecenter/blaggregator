from social.backends.oauth import BaseOAuth2
from urllib import urlencode
import json
import sys

from models import User

def find_legacy_user(strategy, uid, details, user=None, social=None, *args, **kwargs):
    if user or social:
        return None

    users = User.objects.filter(email=details['email'])

    if users:
        return {'user': users[0]}

    users = User.objects.filter(username=details['username'])

    if users:
        return {'user': users[0]}

    return None


class HackerSchoolOAuth2(BaseOAuth2):
    """HackerSchool.com OAuth2 authentication backend"""
    name = 'hackerschool'
    HACKER_SCHOOL_ROOT = 'https://www.hackerschool.com'
    AUTHORIZATION_URL = HACKER_SCHOOL_ROOT + '/oauth/authorize'
    ACCESS_TOKEN_URL = HACKER_SCHOOL_ROOT + '/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REFRESH_TOKEN_URL = ACCESS_TOKEN_URL
    SCOPE_SEPARATOR = ','
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires', 'expires')
    ]

    def get_user_details(self, response):
        """Return user details."""
        first_name = response.get('first_name') or ''
        last_name = response.get('last_name') or ''
        username = first_name + last_name
        return {
                'id':           response.get('id'),
                'email':        response.get('email'),
                'first_name':   first_name,
                'last_name':    last_name,
                'username':     username,
                'avatar_url':   response.get('image'),
                'twitter':      response.get('twitter') or '',
                'github':       response.get('github') or '',
            }

    def get_user_id(self, details, response):
        """Return a unique ID for the current user, by default from server
        response."""
        return response.get('id')

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data."""
        url = self.HACKER_SCHOOL_ROOT + '/api/v1/people/me.json?' + urlencode({
             'access_token': access_token
        })
        try:
            request = self.request(url, method='GET')
            return request.json()
        except ValueError:
            return None
