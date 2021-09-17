from .base import ALLOWED_HOSTS
from .heroku import *  # noqa

ROOT_URL = "https://blag.recurse.com/"
ALLOWED_HOSTS += ["blaggregator-staging.herokuapp.com", "blag.recurse.com"]
AWS_STORAGE_BUCKET_NAME = "blaggregator-staging"
STATIC_URL = "http://" + AWS_STORAGE_BUCKET_NAME + ".s3.amazonaws.com/"
SOCIAL_AUTH_HACKERSCHOOL_REDIRECT_URL = (
    "http://blaggregator-staging.herokuapp.com/complete/hackerschool"
)
