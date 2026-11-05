from .base import ALLOWED_HOSTS
from .heroku import *  # noqa

ROOT_URL = "https://blaggregator.recurse.com/"
ALLOWED_HOSTS += [
    "blaggregator.herokuapp.com",
    "www.blaggregator.us",
    "blaggregator.recurse.com",
]
# Requests via blaggregator.recurse.com reach the app with
# X-Forwarded-Proto=http (an extra proxy hop), so Django sees them as insecure
# and its Origin check rejects the browser's https:// Origin on POSTs.
CSRF_TRUSTED_ORIGINS = [
    "https://blaggregator.recurse.com",
    "https://blaggregator.herokuapp.com",
]
SOCIAL_AUTH_HACKERSCHOOL_REDIRECT_URL = "http://www.blaggregator.us/complete/hackerschool"
