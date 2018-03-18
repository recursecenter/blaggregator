import logging
import os
from urllib import urlencode

import requests
from django.conf import settings
from social_core.backends.oauth import BaseOAuth2

from models import User, Hacker

HACKER_ATTRIBUTES = ('avatar_url', 'twitter', 'github')
USER_FIELDS = ['username', 'email']
log = logging.getLogger("blaggregator")


def create_user(strategy, details, response, uid, user=None, *args, **kwargs):
    if user:
        return

    fields = dict((name, kwargs.get(name) or details.get(name))
                  for name in strategy.setting('USER_FIELDS',
                                               USER_FIELDS))
    # The new user ID should be the same as their ID on hackerschool.com
    fields['id'] = details.get("id")

    if not fields:
        return

    return {
        'is_new': True,
        'user': strategy.create_user(**fields)
    }


def create_or_update_hacker(strategy, details, response, user, *args, **kwargs):
    if hasattr(user, 'hacker'):
        # If there's a hacker already, this is an existing user, and we'll
        # update the hacker.
        hacker = user.hacker
    else:
        # If there's no hacker, that means this is a new user. Let's make the
        # hacker.
        hacker = Hacker(user=user)

    changed = False

    for name, value in details.items():
        if name in HACKER_ATTRIBUTES:
            setattr(hacker, name, value)
            changed = True

    if changed:
        hacker.save()


def update_user_details(user_id):
    params = urlencode({'access_token': settings.HS_PERSONAL_TOKEN})
    path = '/api/v1/people/{}'.format(user_id)
    base_url = HackerSchoolOAuth2.HACKER_SCHOOL_ROOT
    url = '{}{}?{}'.format(base_url, path, params)
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise ValueError('Could not fetch data for {}'.format(user_id))

        hacker_data = HackerSchoolOAuth2.get_user_details(response.json())
        create_or_update_hacker(
            None, hacker_data, None, User.objects.get(id=user_id)
        )
    except Exception as e:
        log.debug('Failed to update user data for hacker %s', user_id)
        log.error(e)


class HackerSchoolOAuth2(BaseOAuth2):
    """HackerSchool.com OAuth2 authentication backend"""

    name = 'hackerschool'
    HACKER_SCHOOL_ROOT = 'https://www.recurse.com'
    AUTHORIZATION_URL = HACKER_SCHOOL_ROOT + '/oauth/authorize'
    ACCESS_TOKEN_URL = HACKER_SCHOOL_ROOT + '/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REFRESH_TOKEN_URL = ACCESS_TOKEN_URL
    SCOPE_SEPARATOR = ','
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires_in', 'expires_in'),
        ('refresh_token', 'refresh_token')
    ]

    def auth_params(self, state=None):
        """Override to allow manually setting redirect_uri."""

        params = super(HackerSchoolOAuth2, self).auth_params(state)
        redirect_uri = os.environ.get('SOCIAL_AUTH_REDIRECT_URI')
        if redirect_uri:
            params['redirect_uri'] = redirect_uri
        return params

    def auth_complete_params(self, state=None):
        """Override to allow manually setting redirect_uri."""
        params = super(HackerSchoolOAuth2, self).auth_complete_params(state)
        redirect_uri = os.environ.get('SOCIAL_AUTH_REDIRECT_URI')
        if redirect_uri:
            params['redirect_uri'] = redirect_uri
        return params

    @staticmethod
    def get_user_details(response):
        """Return user details."""
        first_name = response.setdefault('first_name', '')
        last_name = response.setdefault('last_name', '')
        response['username'] = first_name + last_name
        response['avatar_url'] = response.get('image')
        response.setdefault('github', '')
        response.setdefault('twitter', '')
        return response

    def get_user_id(self, details, response):
        """Return a unique ID for the current user, by default from server
        response."""
        return response.get('id')

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data."""
        url = self.HACKER_SCHOOL_ROOT + '/api/v1/people/me?' + urlencode(
            {'access_token': access_token}
        )
        try:
            request = self.request(url, method='GET')
            return request.json()
        except ValueError:
            return None
