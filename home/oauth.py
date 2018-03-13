import os

from social_core.backends.oauth import BaseOAuth2
from social_django.models import UserSocialAuth
from social_django.strategy import DjangoStrategy
from urllib import urlencode

from models import User, Hacker

HACKER_ATTRIBUTES = ('avatar_url', 'twitter', 'github')
USER_FIELDS = ['username', 'email']


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


def update_user_details(hacker_id, user):
    social_auth = UserSocialAuth.get_social_auth_for_user(user).first()
    strategy = DjangoStrategy(None)
    backend = social_auth.get_backend_instance(strategy)
    try:
        social_auth.refresh_token(strategy)
    except Exception:
        pass  # Ignore failures to refresh token
    url = backend.HACKER_SCHOOL_ROOT + '/api/v1/people/%s?' % hacker_id + urlencode({
        'access_token': social_auth.extra_data['access_token']
    })

    try:
        response = backend.request(url, method='GET')
        hacker_data = backend.get_user_details(response.json())
        create_or_update_hacker(None, hacker_data, None, User.objects.get(id=hacker_id))

    except Exception:
        # It's not very bad, if we are not able to update the userdata... we
        # silently ignore it.
        pass


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

    def get_user_details(self, response):
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
        url = self.HACKER_SCHOOL_ROOT + '/api/v1/people/me?' + urlencode({
            'access_token': access_token
        })
        try:
            request = self.request(url, method='GET')
            return request.json()
        except ValueError:
            return None
