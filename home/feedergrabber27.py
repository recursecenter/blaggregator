#!/usr/bin/python2,7
# feedergrabber27.py
# David Prager Branner
"""Retrieves the links and titles of recent posts from blog feeds."""

from __future__ import print_function

from datetime import datetime
import HTMLParser
import re
import urllib2

import feedparser
import requests

MEDIUM_COMMENT_RE = re.compile('"inResponseToPostId":"\w+"')
CharacterEncodingOverride = feedparser.CharacterEncodingOverride


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
        if link.get('type', '') in (
            'application/atom+xml', 'application/rss+xml'
        ):
            return link.href


def feedergrabber(url):
    """The main function of the module."""
    # Initialize some variables
    post_links_and_titles = []
    # HTML parser to unescape HTML entities
    h = HTMLParser.HTMLParser()
    # Get file contents
    file_contents, errors = retrieve_file_contents(url)
    if file_contents is None:
        return None, errors

    # Gather links, titles, and content
    for entry in file_contents.entries:
        # Ignore posts with 0001-01-01 as published date (A common date for
        # hugo pages)
        post_date = getattr(
            entry, 'published_parsed', getattr(entry, 'updated_parsed', None)
        )
        if post_date and post_date[:6] == datetime.min.timetuple()[:6]:
            errors.append([url + ': Ignoring post with date 0001-01-01.'])
            continue

        # Link
        link = getattr(entry, 'link', '')
        if not link:
            errors.append(
                [url + ': A link was unexpectedly not returned by feedparse.']
            )
            continue

        elif is_medium_comment(link):
            errors.append([url + ': A medium comment link was skipped.'])
            continue

        # Title
        title = getattr(entry, 'title', '')
        if not title:
            errors.append(
                [url + ':A title was unexpectedly not returned by feedparse.']
            )
            continue

        title = h.unescape(title).replace('\n', ' ')
        # Post content
        content = getattr(entry, 'summary', '')
        # Append
        post_links_and_titles.append((link, title, content))
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
