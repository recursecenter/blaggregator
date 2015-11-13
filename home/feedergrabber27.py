#!/usr/bin/python2,7
# feedergrabber27.py
# 20130615, works. See long comment about postprocess; needs fixing with
#    link = u'http://organicdonut.com/?p=224'
# as test.
# David Prager Branner

from __future__ import print_function
import re
import urllib2
import urlparse
import feedparser
import time
import datetime
import HTMLParser

'''Retrieves the links and titles of recent posts from blog feeds.'''

http_pattern = re.compile('^https?://')
reference_pattern = re.compile('^#')
illformed_slash_pattern = re.compile('/\.*(\.|/)+/*')

def retrieve_file_contents(url):
    '''Retrieve file contents from a given URL and log any errors.'''
    try:
        file_contents = feedparser.parse(url)
        errors = None
    except (urllib2.URLError, urllib2.HTTPError) as e:
        # For later: do logging and report at end, along with domain affected
        errors.append([url, e])
        file_contents = None
    return file_contents, errors

def parse_domain(url):
    '''Divide a URL into its three principal parts. Test with no slash at all, multiple slashes. Slashes within remainder should *not* be removed.
    '''
    ParseResult = urlparse.urlparse(url)
    return ParseResult.scheme, ParseResult.netloc, ParseResult.path

def postprocess(link):
    '''Ensures that there is no combination of . or /
    following the initial :// . Test using a range of //, /./, /.../., etc.  '''
    scheme_name, domain, remainder = parse_domain(link)
    remainder = re.sub(illformed_slash_pattern, '/', remainder)
    return scheme_name + '://' + domain + remainder

def check_wellformed(url):
    '''Fix some common minor problems in URL formatting.'''
    # remove any spaces
    url = url.replace(' ', '')
    # make all lower case
    url = url.lower()
    return url

def feedergrabber(url=None):
    '''The main function of the module.'''
    # Initial checks on the URL.
    if not url:
        return None, ['Empty URL.']
    url = check_wellformed(url) # ggg should we include parse_domain here?
    scheme, domain, path = parse_domain(url)
    if not (scheme and domain):
        return None, ['URL malformed: ' + scheme + domain + path]
    # Initialize some variables
    errors = []
    file_contents = ''
    post_links_and_titles = []
    post_date = ''
    # Get file contents
    file_contents, _ = retrieve_file_contents(url)
    # Gather links, titles, and dates
    for i in file_contents.entries:
        # Link
        try:
            link = i.link
        except AttributeError as e:
            errors.append([url +
                    ': A link was unexpectedly not returned by feedparse.'])
            continue
# Have temporarily commented out this call to postprocess;
# its call to parse_domain strips everything after ParseResult.path,
# eliminating a necessary query string. Fix this later. 20130615.
#        link = postprocess(link)
        
        # Title
        try:
            title = i.title
        except AttributeError as e:
            errors.append([url +
                    ':A title was unexpectedly not returned by feedparse.'])
        
        # Unescaping HTML entities
        h = HTMLParser.HTMLParser()
        i.title = h.unescape(title)
        
        # Date
        if i.updated_parsed:
            post_date = i.updated_parsed
        elif i.published_parsed:
            post_date = i.published_parsed
        if post_date:
            post_date = datetime.datetime.fromtimestamp(time.mktime(post_date))
        else:
            post_date = datetime.datetime.now()

        # Post content
        content = getattr(i, 'summary', '')

        # Append
        post_links_and_titles.append((link, i.title, post_date, content))

    if not post_links_and_titles:
        post_links_and_titles = None
        errors.append([url + ': Parsing methods not successful.'])

    return post_links_and_titles, errors
