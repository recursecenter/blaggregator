import os
import dj_database_url
from .base import ALLOWED_HOSTS, DATABASES

ROOT_URL = "https://blaggregator.herokuapp.com/"
# Allowed hostnames
ALLOWED_HOSTS += [
    "blaggregator.herokuapp.com",
    "www.blaggregator.us",
    "blaggregator.recurse.com",
]
# Parse database configuration from $DATABASE_URL
DATABASES["default"] = dj_database_url.config()
# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# S3
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_STORAGE_BUCKET_NAME = "blaggregator"
STATIC_URL = "http://" + AWS_STORAGE_BUCKET_NAME + ".s3.amazonaws.com/"
STATICFILES_STORAGE = "storages.backends.s3boto.S3BotoStorage"
DEFAULT_FILE_STORAGE = "storages.backends.s3boto.S3BotoStorage"
# Social Auth
SOCIAL_AUTH_HACKERSCHOOL_REDIRECT_URL = (
    "http://www.blaggregator.us/complete/hackerschool"
)
