from __future__ import print_function

# Standard library
import logging
from urlparse import urlparse

# 3rd-party library
from django.core.management.base import BaseCommand
from django.db.models import Count
import grequests

# Local library
from home.models import Blog, Post

log = logging.getLogger("blaggregator")


class Command(BaseCommand):
    help = 'Remove posts with duplicated titles.'

    def handle(self, **options):
        delete_duplicate_title_posts()


def delete_duplicate_title_posts():
    for blog, titles in iter_blogs_with_duplicate_titles():
        # Get the base_url for the blog
        parsed_url = urlparse(blog.feed_url)
        base_url = '{}://{}'.format(parsed_url.scheme, parsed_url.netloc)
        print('Fetching posts for {}'.format(base_url))
        urls = set()
        # Delete posts if we can uniquify with base name otherwise collect urls
        for title, posts in iter_posts_with_duplicate_titles(blog, titles):
            base_url_matches = posts.filter(url__startswith=base_url)
            if base_url_matches.count() == 1:
                # Delete all other posts, if there's only post starting with base_url
                keep = base_url_matches.first().id
                posts.exclude(id=keep).delete()
            else:
                urls = urls.union(set(posts.values_list('url', flat=True)))
        if not urls:
            continue

        # Do web requests to figure out which URLs still work
        urls = list(urls)
        print('Requesting {} urls'.format(len(urls)))
        requests = (
            grequests.get(u, allow_redirects=True, timeout=30) for u in urls
        )
        responses = grequests.map(requests)
        successful = dict(filter(filter_successful, zip(urls, responses)))
        # Delete duplicate posts based on successful get or keep latest post ####
        for title, posts in iter_posts_with_duplicate_titles(blog, titles):
            for post in posts:
                if post.url in successful:
                    posts.exclude(id=post.id).delete()
                    break

            else:
                posts.exclude(id=posts.first().id).delete()


def filter_successful(pair):
    (url, response) = pair
    return response is not None and response.status_code == 200


def iter_blogs_with_duplicate_titles():
    for blog in Blog.objects.all():
        # Collect all duplicate titles
        posts = Post.objects.filter(blog=blog)
        duplicate_titles = posts.values('title').annotate(
            Count('id')
        ).order_by(
        ).filter(
            id__count__gt=1
        )
        if not duplicate_titles.exists():
            continue

        yield blog, duplicate_titles


def iter_posts_with_duplicate_titles(blog, titles):
    for title in titles:
        duplicate_posts = Post.objects.filter(
            blog=blog, title=title['title']
        ).distinct(
        )
        if duplicate_posts.count() <= 1:
            continue

        yield title, duplicate_posts
