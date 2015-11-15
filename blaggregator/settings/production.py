import os

# NOTE: We import staging (not base) and override any settings that need to be!
from staging import *

AWS_STORAGE_BUCKET_NAME = 'blaggregator'
STATIC_URL = 'http://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'
ALLOWED_HOSTS = ['blaggregator.herokuapp.com', 'www.blaggregator.us']
SOCIAL_AUTH_HACKERSCHOOL_REDIRECT_URL = 'http://www.blaggregator.us/complete/hackerschool'
