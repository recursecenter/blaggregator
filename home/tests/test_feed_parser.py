from io import BytesIO
import datetime
from functools import partial
import re

from django.test import TestCase
from hypothesis import given, HealthCheck, note, settings
from mock import patch

from home.feedergrabber27 import feedergrabber
from home.tests.utils import generate_full_feed

MIN_DATE_FEED = b"""
<?xml version="1.0" encoding="utf-8" standalone="yes" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Max.Computer</title>
    <link>http://max.computer/</link>
    <language>en-US</language>
    <atom:link href="http://max.computer/index.xml" rel="self" type="application/rss+xml" />
    <item>
      <title>About</title>
      <link>http://max.computer/about/</link>
      <pubDate>Mon, 01 Jan 0001 00:00:00 +0000</pubDate>
      <guid>http://max.computer/about/</guid>
      <description>About me</description>
    </item>
  </channel>
</rss>
"""


class FeedParserTestCase(TestCase):
    @given(generate_full_feed())
    @settings(max_examples=1000, suppress_health_check=[HealthCheck.too_slow])
    def test_parsing_valid_feeds(self, feed):
        note(feed.feed)
        note(feed.items)
        with patch(
            "urllib.request.OpenerDirector.open",
            new=partial(self.patch_open, feed),
        ):
            contents, errors = feedergrabber(feed.feed["link"])
            if contents is None:
                note(errors)
                self.assertEqual(0, len(feed.items))
                self.assertEqual(1, len(errors))
                self.assertIn("Parsing methods not successful", errors[0])
            else:
                for i, (link, title, date, content) in enumerate(contents):
                    item = feed.items[i]
                    self.assertEqual(link, item["link"])
                    item_date = item.get("pubdate", item.get("updateddate"))
                    note(item_date)
                    note(date)
                    self.assertIsNotNone(date)
                    self.assertGreaterEqual(
                        datetime.datetime.now().utctimetuple(),
                        date.utctimetuple(),
                    )

    @given(generate_full_feed())
    @settings(max_examples=1000, suppress_health_check=[HealthCheck.too_slow])
    def test_parsing_broken_feeds(self, feed):
        note(feed.feed)
        note(feed.items)
        with patch(
            "urllib.request.OpenerDirector.open",
            new=partial(self.patch_open_broken_feed, feed),
        ):
            contents, errors = feedergrabber(feed.feed["link"])
            note(contents)
            note(errors)
            self.assertIsNone(contents)
            self.assertEqual(len(feed.items) + 1, len(errors))
            self.assertIn("Parsing methods not successful", errors[-1])

    @staticmethod
    def patch_open(feed, url, data=None, timeout=None):
        xml = feed.writeString("utf8")
        note(xml)
        return BytesIO(xml.encode("utf8"))

    @staticmethod
    def patch_open_broken_feed(feed, url, data=None, timeout=None):
        xml = FeedParserTestCase.patch_open(feed, url, data, timeout)
        text = xml.read().decode("utf8")
        text = text.replace('encoding="utf8"', "")
        # feedgenerator makes title and link mandatory, hence we remove from
        # generated xml.
        if len(feed.items) % 2 == 0:
            # Strip off entry titles
            text = re.sub(
                "(<entry>.*?)(<title>.*?</title>)(.*?</entry>)", "\\1\\3", text
            )
            # Strip off item titles
            text = re.sub(
                "(<item>.*?)(<title>.*?</title>)(.*?</item>)", "\\1\\3", text
            )
        else:
            # Strip off entry links
            text = re.sub(
                "(<entry>.*?)(<link.*?>.*?</link>)(.*?</entry>)",
                "\\1\\3",
                text,
            )
            # Strip off item links
            text = re.sub(
                "(<item>.*?)(<link.*?>.*?</link>)(.*?</item>)", "\\1\\3", text
            )
            # Strip off entry ids
            text = re.sub(
                "(<entry>.*?)(<id.*?>.*?</id>)(.*?</entry>)", "\\1\\3", text
            )
            # Strip off item ids
            text = re.sub(
                "(<item>.*?)(<id.*?>.*?</id>)(.*?</item>)", "\\1\\3", text
            )
        note(text)
        return BytesIO(text.encode("utf8"))


class FeedParserHelpersTestCase(TestCase):
    def test_parsing_feeds_with_min_dates(self):
        with patch(
            "urllib.request.OpenerDirector.open", new=self.min_date_feed
        ):
            contents, errors = feedergrabber("http://max.computer/index.html")
            self.assertIsNone(contents)
            self.assertEqual(2, len(errors))
            self.assertIn("Parsing methods not successful", errors[-1])
            self.assertIn("hugo page", errors[0])

    @staticmethod
    def min_date_feed(*args, **kwargs):
        return BytesIO(MIN_DATE_FEED.strip())
