# Standard library
from __future__ import print_function
from datetime import timedelta
import logging

# 3rd-party library
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

# Local library
from home.models import Blog, User
from home.zulip_helpers import notify_uncrawlable_blogs, guess_zulip_emails

log = logging.getLogger("blaggregator")


class Command(BaseCommand):
    help = 'Notify owners of blogs with failing crawls.'

    def handle(self, **options):
        last_week = timezone.now() - timedelta(days=7)
        flagging_filter = (
            Q(last_crawled=None) | Q(last_crawled__lt=last_week)
        ) & Q(
            skip_crawl=False
        )
        flagged_blogs = Blog.objects.filter(flagging_filter).distinct()
        log.debug(
            'Notifying %s blog owners about blog crawling errors',
            flagged_blogs.count(),
        )
        if not settings.DEBUG:
            yes_or_no = raw_input('Are you sure you want to continue? [y/N]: ')
            if yes_or_no.lower().strip()[:1] != 'y':
                return

        # Skip crawls on these blogs in future, until the feed_url changes
        notified = set()
        notify_failed = set()
        users = flagged_blogs.order_by('user').distinct('user').values_list(
            'user', flat=True
        )
        for user in guess_zulip_emails(User.objects.filter(id__in=users)):
            blogs = flagged_blogs.filter(user=user)
            if notify_uncrawlable_blogs(user, blogs, debug=settings.DEBUG):
                notified.add(user.email)
            else:
                notify_failed.add(user.email)
        # Logging notification success/failure
        if notified:
            flagged_blogs.filter(user__email__in=notified).update(
                skip_crawl=True
            )
            log.debug(
                'Notified %s blog owners and turned off crawling',
                len(notified),
            )
        if notify_failed:
            log.debug('Failed to notify %s users:', len(notify_failed))
            log.debug(u'\n'.join(notify_failed))
