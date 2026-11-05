from .base import ALLOWED_HOSTS
from .heroku import *  # noqa

ROOT_URL = "https://blag.recurse.com/"
ALLOWED_HOSTS += ["blaggregator-staging.herokuapp.com", "blag.recurse.com"]
CSRF_TRUSTED_ORIGINS = [
    "https://blag.recurse.com",
    "https://blaggregator-staging.herokuapp.com",
]
SOCIAL_AUTH_HACKERSCHOOL_REDIRECT_URL = (
    "http://blaggregator-staging.herokuapp.com/complete/hackerschool"
)
