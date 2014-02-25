from social.backends.oauth import BaseOAuth2
from urllib import urlencode
import json
import sys

from models import User

def find_legacy_user(strategy, uid, details, user=None, social=None, *args, **kwargs):
    # user is present if we're currently logged in (very unlikely given there's no
    # link to /login/hackerschool when you are logged in).
    #
    # social is present if we've already oauthed with hackerschool.com before.
    # If this is the case, we don't need to find the legacy user.
    # Social.pipeline.social_auth.social_user sets user from social.
    if user or social:
        return None

    # first try finding a legacy account by matching the email returned from
    # the API. This won't always work because people can change their emails on
    # hackerschool.com.
    users = User.objects.filter(email=details['email'])

    if users:
        return {'user': users[0]}

    # Fall back on matching by username. People can't change thier names on
    # hackerschool.com. We tried email first because email addresses are
    # globally unique, while it's possible that two people might have the same
    # name and thus username.
    users = User.objects.filter(username=details['username'])

    if users:
        return {'user': users[0]}

    # If we get down here, we're almost certainly dealing with a new uesr.
    # Social.pipeline.user.create_user will make a new user shortly after this.
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
