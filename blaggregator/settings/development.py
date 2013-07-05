# -*- coding: utf-8 -*-
from base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'blaggregator_dev',
        'USER': 'PuercoPop',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

ALLOWED_HOSTS += ['localhost', '127.0.0.1']
