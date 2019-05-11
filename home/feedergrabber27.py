#!/usr/bin/python2,7
# feedergrabber27.py
# David Prager Branner
"""Retrieves the links and titles of recent posts from blog feeds."""

from __future__ import print_function

import datetime
import HTMLParser
import socket
import urllib2

import feedparser

from .utils import is_medium_comment


CharacterEncodingOverride = feedparser.CharacterEncodingOverride
# Set a timeout of 60 seconds for sockets - useful when crawling some blogs
socket.setdefaulttimeout(60)


def retrieve_file_contents(url):
    """Retrieve file contents from a given URL and log any errors."""
    errors = []
    try:
        file_contents = feedparser.parse(url)
    except (urllib2.URLError, urllib2.HTTPError) as e:
        errors.append("Fetching content for {} failed: {}".format(url, e))
        file_contents = None
    return file_contents, errors


def find_feed_url(parsed_content):
    """Try to find the feed url from parsed content."""
    try:
        links = parsed_content.feed.links
    except AttributeError:
        links = []
    for link in links:
        if link.get("type", "") in (
            "application/atom+xml",
            "application/rss+xml",
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

    # Gather links, titles, dates and content
    for entry in file_contents.entries:
        # Link
        link = getattr(entry, "link", "")
        if not link:
            errors.append("No link was found for post: {}".format(url))
            continue

        elif is_medium_comment(entry):
            errors.append("A medium comment was skipped: {}".format(link))
            continue

        # Title
        title = getattr(entry, "title", "")
        if not title:
            errors.append("No title was returned for post: {}.".format(link))
            continue

        title = h.unescape(title).replace("\n", " ")
        # Date
        post_date = getattr(
            entry, "published_parsed", getattr(entry, "updated_parsed", None)
        )
        now = datetime.datetime.now()
        if post_date is None:
            # No date posts are marked as crawled now
            post_date = now
        else:
            post_date = datetime.datetime(*post_date[:6])
            # future dated posts are marked as crawled now
            if post_date > now:
                post_date = now
            # posts dated 0001-01-01 are ignored -- common for _pages_ in hugo feeds
            elif post_date == datetime.datetime.min:
                errors.append("Has min date - hugo page?: {}".format(link))
                continue

        # Post content
        content = getattr(entry, "summary", "")
        # Append
        post_links_and_titles.append((link, title, post_date, content))
    if len(post_links_and_titles) == 0:
        post_links_and_titles = None
        errors.append(url + ": Parsing methods not successful.")
    return post_links_and_titles, errors
