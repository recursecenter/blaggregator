from social.backends.oauth import BaseOAuth2
            
class HackerSchoolOAuth2(BaseOAuth2):
    """HackerSchool.com OAuth2 authentication backend"""
    name = 'hackerschool'
    AUTHORIZATION_URL = 'https://www.hackerschool.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://www.hackerschool.com/oauth/token'
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
        return {
                'id':           response.get('id'),
                'email':        response.get('email'),
                'first_name':   response.get('first_name') or '',
                'last_name':    response.get('last_name') or '',
                'username':     first_name + last_name,
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
        url = 'http://www.hackerschool.com/api/v1/people/me.json' + urlencode({
            'access_token': access_token
        })
        try:
            return json.load(self.urlopen(url))
        except ValueError:
            return None