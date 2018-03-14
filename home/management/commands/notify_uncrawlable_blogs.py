# Standard library
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
        flagging_filter = Q(last_crawled=None) | Q(last_crawled__lt=last_week)
        flagged_blogs = Blog.objects.filter(flagging_filter)

        log.debug('Notifying %s blog owners about blog crawling errors', flagged_blogs.count())
        if not settings.DEBUG:
            yes_or_no = raw_input('Are you sure you want to continue? [y/N]: ')
            if yes_or_no.lower().strip()[:1] != 'y':
                return

        for blog in flagged_blogs:
            notify_uncrawlable_blog(blog, debug=settings.DEBUG)
        log.debug('Notified %s blog owners', flagged_blogs.count())
