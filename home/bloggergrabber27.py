#!/usr/bin/python2,7
# bloggergrabber.py
# 20130418, works.
# David Prager Branner
'''Given a URL, attempts to download the related web page and from it isolate
the URLs and titles of blog posts.

If "select_strings" is specified, will use the contents of that list to help
parse the web page; if not specified, will use the three most commonly seen
patterns (associated with feeds) to parse the file.'''

import re
import urllib2
import bs4
import urlparse

http_pattern = re.compile('^https?://')
reference_pattern = re.compile('^#')
illformed_slash_pattern = re.compile('/\.*(\.|/)+/*')

def retrieve_file_contents(url):
    try:
        the_request = urllib2.Request(url)
    except (urllib2.URLError, urllib2.HTTPError) as e:
        # For later: do logging and report at end, along with domain affected
        errors.append([url, e])
        return None, errors
    the_response = urllib2.urlopen(the_request)
    file_contents =  the_response.read()
    return file_contents.decode('utf-8'), None

def parse_domain(url):
    '''Divide a URL into its three principal parts. Test with no slash at all, multiple slashes. Slashes within remainder should *not* be removed.
    '''
    ParseResult = urlparse.urlparse(url)
    return ParseResult.scheme, ParseResult.netloc, ParseResult.path

def add_domain_to_any_relative_URI(scheme, domain, link, title,
            post_links_and_titles):
    '''If link begins with anything other than http://, https://, or #, add http:// to it.  Test with http and #, perh also http:// and https, all at start of string. Perhaps also with these not at start?
    '''
    if not ((re.search(http_pattern, str(link)) or
            re.search(reference_pattern, str(link)))):
        link = re.sub('^', scheme+'://'+domain+'/', str(link))
    if not title:
        title = 'No title found.'
    post_links_and_titles.append((link, title))
    return post_links_and_titles

def postprocess(link):
    '''Ensures that there is no combination of . or /
    following the initial :// . Test using a range of //, /./, /.../., etc.  '''
    scheme_name, domain, remainder = parse_domain(link)
    remainder = re.sub(illformed_slash_pattern, '/', remainder)
    return scheme_name + '://' + domain + remainder

def check_wellformed(url):
    # ggg this still needs to be written)
    # ggg Should look at urllib.parse.urlparse before proceeding.
    # remove any spaces
    url = url.replace(' ', '')
    # make all lower case
    url = url.lower()
    # fix "htp"
    # if no scheme name at start, place one at start
    # if ill-formed delimiter (:/ or //), replace
    # if no ://, then check for http or http at start and place delimiter next
    #
    return url

def bloggergrabber(url=None, select_strings=None):
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
    if not select_strings:
        select_strings = [
                ['item link',
                    'item title',
                    lambda link: link.text,
                    lambda title: title.text],
                ['entry link[rel="alternate"]',
                    'entry title[type="text"]',
                    lambda link: link.attrs.get('href'),
                    lambda title: title.text],
                ['entry link',
                    'entry title',
                    lambda link: link.attrs.get('href'),
                    lambda title: title.text]
            ]
    # Get file contents
    file_contents, _ = retrieve_file_contents(url)
    # Parse HTML
    try:
        soup = bs4.BeautifulSoup(file_contents)
    except Exception as e:
        errors.append([url, e])
        return None, errors
    # Gather links and titles
    for option in select_strings:
        link_option = soup.select(option[0])
        title_option = soup.select(option[1])
        if link_option and title_option:
            for link, title in zip(link_option, title_option):
    #            print('link before:', link)
                link = option[2](link)
    #            print('link after:', link)
    #            print('title before:', title)
                title = option[3](title)
    #            print('title after:', title)
                post_links_and_titles = add_domain_to_any_relative_URI(scheme,
                        domain, link, title, post_links_and_titles)
            break
    if not post_links_and_titles:
        post_links_and_titles = None
        errors.append(url + ': Parsing methods not successful.')
    return post_links_and_titles, errors
