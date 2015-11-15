import os

from _base import *

# S3
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = 'blaggregator-staging'

STATIC_URL = 'http://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'
STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

ALLOWED_HOSTS = ['blaggregator-staging.herokuapp.com']

SOCIAL_AUTH_HACKERSCHOOL_REDIRECT_URL = 'http://blaggregator-staging.herokuapp.com/complete/hackerschool'

# This bit uses the module dj_database_url to manage databases based on the
# url of the database, as configured in environmental variables (which are
# in turn managed by the Heroku Postgres add-on)

# Parse database configuration from $DATABASE_URL
import dj_database_url
DATABASES['default'] = dj_database_url.config()

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
