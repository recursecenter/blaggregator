from cStringIO import StringIO
import datetime

from django.test import TestCase
from hypothesis import given, HealthCheck, note, settings
from mock import patch

from home.feedergrabber27 import feedergrabber
from home.tests.utils import generate_feed, generate_items


class FeedParserTestCase(TestCase):

    @given(generate_feed(), generate_items())
    @settings(max_examples=1000, suppress_health_check=[HealthCheck.too_slow])
    def test_parsing_valid_feeds(self, feed, items):

        def _open(url, data=None, timeout=None):
            xml = feed.writeString('utf8')
            note(xml)
            return StringIO(xml)

        for item in items:
            feed.add_item(**item)

        note(feed.feed)
        note(feed.items)

        with patch('urllib2.OpenerDirector.open', new=_open):
            contents, errors = feedergrabber(feed.feed['link'])
            if contents is None:
                note(errors)
                self.assertEqual(0, len(feed.items))
                self.assertEqual(1, len(errors))
                self.assertIn('Parsing methods not successful', errors[0][0])

            else:
                self.assertEqual(len(items), len(feed.items))
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
