# Standard library
import logging

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
    # Collect URLs of all duplicate title posts
    urls = set()
    for (title, posts) in iter_duplicated_posts():
        post_urls = set(posts.values_list('url', flat=True))
        urls = urls.union(post_urls)
    urls = list(urls)
    # Do web requests to figure out which of these are valid URLs
    responses = []
    N = int(len(urls) / 100) + 1  # Split into batches of 100 to track progress
    print("Sending requests for {} urls".format(len(urls)))
    for i in range(N):
        print('Fetching first {}00 urls'.format(i + 1))
        requests = (
            grequests.get(u, allow_redirects=True, timeout=30)
            for u in urls[i * 100: (i + 1) * 100]
        )
        responses.extend(grequests.map(requests))
    successful = dict(filter(filter_successful, zip(urls, responses)))
    # Keep posts with valid URLs
    for (title, posts) in iter_duplicated_posts():
        for post in posts:
            if post.url in successful:
                keep = post.id
                break

        else:
            # If no url is working, keep the latest post
            keep = posts.first().id
        posts.exclude(id=keep).delete()


def filter_successful(pair):
    (url, response) = pair
    return response is not None and response.status_code == 200


def iter_duplicated_posts():
    for blog in Blog.objects.all():
        posts = Post.objects.filter(blog=blog)
        duplicate_titles = posts.values('title').annotate(
            Count('id')
        ).order_by(
        ).filter(
            id__count__gt=1
        )
        for title in duplicate_titles:
            posts = Post.objects.filter(
                blog=blog, title=title['title']
            ).distinct(
            )
            yield title, posts
