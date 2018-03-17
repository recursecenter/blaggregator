# Standard library
from __future__ import print_function
from datetime import datetime, timedelta
import logging

# 3rd-party library
from django.db.models import Q
from django.core.management.base import BaseCommand
from django.conf import settings

# Local library
from home.models import Blog
from home.zulip_helpers import notify_uncrawlable_blog

log = logging.getLogger("blaggregator")


class Command(BaseCommand):
    help = 'Notify owners of blogs with failing crawls.'

    def handle(self, **options):
        last_week = datetime.now() - timedelta(days=7)
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
        for blog in flagged_blogs:
            if notify_uncrawlable_blog(blog, debug=settings.DEBUG):
                notified.add(blog.id)
            else:
                notify_failed.add(blog.id)
        if notified:
            Blog.objects.filter(id__in=notified).update(skip_crawl=True)
            log.debug(
                'Notified %s blog owners and turned off crawling',
                len(notified),
            )
        if notify_failed:
            emails = Blog.objects.filter(id__in=notify_failed).values_list(
                'user__email', flat=True
            )
            log.debug('Failed to notify %s users:', len(notify_failed))
            log.debug(u'\n'.join(emails))
