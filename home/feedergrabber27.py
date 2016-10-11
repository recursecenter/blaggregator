#!/usr/bin/python2,7
# feedergrabber27.py
# 20130615, works. See long comment about postprocess; needs fixing with
#    link = u'http://organicdonut.com/?p=224'
# as test.
# David Prager Branner

"""Retrieves the links and titles of recent posts from blog feeds."""

from __future__ import print_function
import re
import urllib2
import urlparse
import feedparser
import time
import datetime
import HTMLParser

http_pattern = re.compile('^https?://')
reference_pattern = re.compile('^#')
illformed_slash_pattern = re.compile('/\.*(\.|/)+/*')


def retrieve_file_contents(url, errors):
    '''Retrieve file contents from a given URL and log any errors.'''
    try:
        file_contents = feedparser.parse(url)
    except (urllib2.URLError, urllib2.HTTPError) as e:
        # For later: do logging and report at end, along with domain affected
        errors.append([url, e])
        file_contents = None
    return file_contents, errors


def parse_domain(url):
    '''Divide a URL into its three principal parts.

    Test with no slash at all, multiple slashes. Slashes within remainder
    should *not* be removed.

    '''

    ParseResult = urlparse.urlparse(url)
    return ParseResult.scheme, ParseResult.netloc, ParseResult.path


def check_wellformed(url):
    '''Fix some common minor problems in URL formatting.'''
    # remove any spaces
    url = url.replace(' ', '')
    # make all lower case
    url = url.lower()
    return url


def find_feed_url(parsed_content):
    """Try to find the feed url from parsed content."""
    try:
        links = parsed_content.feed.links
    except AttributeError:
        links = []

    for link in links:
        if link.get('type', '') in ('application/atom+xml', 'application/rss+xml'):
            return link.href


def feedergrabber(url=None, suggest_feed_url=False):
    """The main function of the module."""

    # Initial checks on the URL.
    if not url:
        return None, ['Empty URL.']
    url = check_wellformed(url)  # ggg should we include parse_domain here?
    scheme, domain, path = parse_domain(url)
    if not (scheme and domain):
        return None, ['URL malformed: ' + scheme + domain + path]

    # Initialize some variables
    errors = []
    post_links_and_titles = []

    # Get file contents
    file_contents, _ = retrieve_file_contents(url, errors)

    if file_contents is None:
        return None, errors

    elif file_contents.bozo and not isinstance(file_contents.bozo_exception, feedparser.CharacterEncodingOverride):
        feed_url = find_feed_url(file_contents) if suggest_feed_url else None
        return None, [{'feed_url': feed_url, 'url': url, 'error': file_contents.bozo_exception}]

    # Gather links, titles, and dates
    for i in file_contents.entries:
        # Link
        try:
            link = i.link
        except AttributeError:
            errors.append([url +
                           ': A link was unexpectedly not returned by feedparse.'])
            continue

        # Title
        try:
            title = i.title
        except AttributeError:
            errors.append([url +
                           ':A title was unexpectedly not returned by feedparse.'])

        # Unescaping HTML entities
        h = HTMLParser.HTMLParser()
        i.title = h.unescape(title)

        # Date
        post_date = None
        for name in ('published_parsed', 'updated_parsed'):
            if name in i:
                post_date = getattr(i, name)
                break

        now = datetime.datetime.now()
        if post_date is None:
            # No date posts are marked as crawled now
            post_date = now

        else:
            post_date = datetime.datetime(*post_date[:6])
            # future dated posts are marked as crawled now
            if post_date > now:
                post_date = now

        # Append
        post_links_and_titles.append((link, i.title, post_date))

    if len(post_links_and_titles) == 0:
        post_links_and_titles = None
        errors.append([url + ': Parsing methods not successful.'])

    return post_links_and_titles, errors
