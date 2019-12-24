# Standard library

import logging

# 3rd-party library
from django.core.management.base import BaseCommand

# Local library
from home.models import User
from home.oauth import update_user_details

log = logging.getLogger("blaggregator")


class Command(BaseCommand):
    help = 'Update user details from RC API.'

    def handle(self, **options):
        users = User.objects.exclude(hacker=None)
        log.debug('Updating %s users', users.count())
        for user_id in users.values_list('id', flat=True):
            log.debug('Updating user: %s', user_id)
            update_user_details(user_id)
