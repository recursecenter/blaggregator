from social.backends.oauth import BaseOAuth2
from urllib import urlencode
import json
import sys
            
class HackerSchoolOAuth2(BaseOAuth2):
    """HackerSchool.com OAuth2 authentication backend"""
    name = 'hackerschool'
    HACKERSCHOOL_ROOT = 'https://www.hackerschool.com'
    AUTHORIZATION_URL = HACKERSCHOOL_ROOT + '/oauth/authorize'
    ACCESS_TOKEN_URL = HACKERSCHOOL_ROOT + '/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_URL = 'http://localhost:4000/complete/hackerschool/' #todo prodify
    # REDIRECT_URL = 'urn:ietf:wg:oauth:2.0:oob'
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
        url = self.HACKERSCHOOL_ROOT + '/api/v1/people/me.json?' + urlencode({
             'access_token': access_token
        })
        try:
            request = self.request(url, method='GET')
            return request.json() 
        except ValueError:
            return None
