from cStringIO import StringIO
import datetime
from functools import partial
import re

from django.test import TestCase
from hypothesis import given, HealthCheck, note, settings
from mock import patch

from home.feedergrabber27 import feedergrabber
from home.tests.utils import generate_full_feed


class FeedParserTestCase(TestCase):

    @given(generate_full_feed())
    @settings(max_examples=1000, suppress_health_check=[HealthCheck.too_slow])
    def test_parsing_valid_feeds(self, feed):

        note(feed.feed)
        note(feed.items)

        with patch('urllib2.OpenerDirector.open', new=partial(self.patch_open, feed)):
            contents, errors = feedergrabber(feed.feed['link'])
            if contents is None:
                note(errors)
                self.assertEqual(0, len(feed.items))
                self.assertEqual(1, len(errors))
                self.assertIn('Parsing methods not successful', errors[0][0])

            else:
                for i, (link, title, date, content) in enumerate(contents):
                    item = feed.items[i]
                    self.assertEqual(link, item['link'])
                    item_date = item.get('pubdate', item.get('updateddate'))
                    note(item_date)
                    note(date)
                    self.assertIsNotNone(date)
                    self.assertGreaterEqual(
                        datetime.datetime.now().utctimetuple(), date.utctimetuple()
                    )

    @given(generate_full_feed())
    @settings(max_examples=1000, suppress_health_check=[HealthCheck.too_slow])
    def test_parsing_broken_feeds(self, feed):

        note(feed.feed)
        note(feed.items)

        with patch('urllib2.OpenerDirector.open', new=partial(self.patch_open_broken_feed, feed)):
            contents, errors = feedergrabber(feed.feed['link'])
            note(contents)
            note(errors)
            self.assertIsNone(contents)
            self.assertEqual(len(feed.items) + 1, len(errors))
            self.assertIn('Parsing methods not successful', errors[-1][0])

    @staticmethod
    def patch_open(feed, url, data=None, timeout=None):
        xml = feed.writeString('utf8')
        note(xml)
        return StringIO(xml)

    @staticmethod
    def patch_open_broken_feed(feed, url, data=None, timeout=None):
        xml = FeedParserTestCase.patch_open(feed, url, data, timeout)
        text = xml.read()
        text = text.replace('encoding="utf8"', '')
        # feedgenerator makes title and link mandatory, hence we remove from
        # generated xml.
        if len(feed.items) % 2 == 0:
            # Strip off entry titles
            text = re.sub("(<entry>.*?)(<title>.*?</title>)(.*?</entry>)", "\\1\\3", text)
            # Strip off item titles
            text = re.sub("(<item>.*?)(<title>.*?</title>)(.*?</item>)", "\\1\\3", text)
        else:
            # Strip off entry links
            text = re.sub("(<entry>.*?)(<link.*?>.*?</link>)(.*?</entry>)", "\\1\\3", text)
            # Strip off item links
            text = re.sub("(<item>.*?)(<link.*?>.*?</link>)(.*?</item>)", "\\1\\3", text)
            # Strip off entry ids
            text = re.sub("(<entry>.*?)(<id.*?>.*?</id>)(.*?</entry>)", "\\1\\3", text)
            # Strip off item ids
            text = re.sub("(<item>.*?)(<id.*?>.*?</id>)(.*?</item>)", "\\1\\3", text)
        note(text)
        return StringIO(text)
