#!/usr/bin/python2,7
# feedergrabber27.py
# David Prager Branner

"""Retrieves the links and titles of recent posts from blog feeds."""

from __future__ import print_function

import datetime
import HTMLParser
import re
import urllib2

import feedparser
import requests

MEDIUM_COMMENT_RE = re.compile('"inResponseToPostId":"\w+"')


def retrieve_file_contents(url):
    '''Retrieve file contents from a given URL and log any errors.'''
    errors = []
    try:
        file_contents = feedparser.parse(url)
    except (urllib2.URLError, urllib2.HTTPError) as e:
        errors.append([url, e])
        file_contents = None
    return file_contents, errors


def find_feed_url(parsed_content):
    """Try to find the feed url from parsed content."""
    try:
        links = parsed_content.feed.links
    except AttributeError:
        links = []

    for link in links:
        if link.get('type', '') in ('application/atom+xml', 'application/rss+xml'):
            return link.href


def feedergrabber(url, suggest_feed_url=False):
    """The main function of the module."""

    # Initialize some variables
    post_links_and_titles = []
    # HTML parser to unescape HTML entities
    h = HTMLParser.HTMLParser()

    # Get file contents
    file_contents, errors = retrieve_file_contents(url)

    if file_contents is None:
        return None, errors

    elif file_contents.bozo and not isinstance(file_contents.bozo_exception, feedparser.CharacterEncodingOverride):
        feed_url = find_feed_url(file_contents) if suggest_feed_url else None
        suggestion = [{'feed_url': feed_url, 'url': url, 'error': file_contents.bozo_exception}]
        return None, suggestion

    # Gather links, titles, and dates
    for entry in file_contents.entries:
        # Link
        link = getattr(entry, 'link', '')
        if not link:
            errors.append([url + ': A link was unexpectedly not returned by feedparse.'])
            continue

        elif is_medium_comment(link):
            errors.append([url + ': A medium comment link was skipped.'])
            continue

        # Title
        title = getattr(entry, 'title', '')
        if not title:
            errors.append([url + ':A title was unexpectedly not returned by feedparse.'])
            continue
        title = h.unescape(title)

        # Date
        post_date = getattr(entry, 'published_parsed', getattr(entry, 'updated_parsed', None))
        now = datetime.datetime.now()
        if post_date is None:
            # No date posts are marked as crawled now
            post_date = now

        else:
            post_date = datetime.datetime(*post_date[:6])
            # future dated posts are marked as crawled now
            if post_date > now:
                post_date = now

        # Post content
        content = getattr(entry, 'summary', '')

        # Append
        post_links_and_titles.append((link, title, post_date, content))

    if len(post_links_and_titles) == 0:
        post_links_and_titles = None
        errors.append([url + ': Parsing methods not successful.'])

    return post_links_and_titles, errors


def is_medium_comment(link):
    """Check if a link is a medium comment."""

    if 'medium.com' not in link:
        return False

    try:
        content = requests.get(link).content
        is_comment = re.search(MEDIUM_COMMENT_RE, content) is not None

    except Exception:
        is_comment = False

    return is_comment
