import datetime
from functools import partial

from django.test import TestCase
from mock import patch

from home.feedergrabber27 import feedergrabber
from home.tests.utils import generate_full_feed, fake_response

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
    def test_parsing_valid_feeds(self):
        feed = generate_full_feed()
        with patch(
            "urllib.request.OpenerDirector.open",
            new=partial(self.patch_open, feed),
        ):
            contents, errors = feedergrabber(feed.feed["link"])
            if contents is None:
                self.assertEqual(0, len(feed.items))
                self.assertEqual(1, len(errors))
                self.assertIn("Parsing methods not successful", errors[0])
            else:
                for i, (link, title, date, content) in enumerate(contents):
                    item = feed.items[i]
                    self.assertEqual(link, item["link"])
                    self.assertIsNotNone(date)
                    self.assertGreaterEqual(
                        datetime.datetime.now().utctimetuple(),
                        date.utctimetuple(),
                    )

    def test_parsing_broken_feeds(self):
        feed = generate_full_feed()
        with patch(
            "urllib.request.OpenerDirector.open",
            new=partial(self.patch_open_broken_feed, feed),
        ):
            contents, errors = feedergrabber(feed.feed["link"])
            self.assertIsNone(contents)
            self.assertEqual(len(feed.items) + 1, len(errors))
            self.assertIn("Parsing methods not successful", errors[-1])

    @staticmethod
    def patch_open(feed, url, data=None, timeout=None):
        return fake_response(feed.writeString("utf8").encode("utf8"))()

    @staticmethod
    def patch_open_broken_feed(feed, url, data=None, timeout=None):
        xml = FeedParserTestCase.patch_open(feed, url, data, timeout)
        text = xml.read().decode("utf8")
        text = text.replace('encoding="utf8"', "")
        # feedgenerator makes title and link mandatory, hence we remove from
        # generated xml.
        if len(feed.items) % 2 == 0:
            feed.feed["title"] = None
            for item in feed.items:
                item["title"] = None
        else:
            feed.feed["link"] = None
            feed.feed["id"] = None
            for item in feed.items:
                item["link"] = None
                item["id"] = None
        return fake_response(feed.writeString("utf8").encode("utf8"))()


class FeedParserHelpersTestCase(TestCase):
    def test_parsing_feeds_with_min_dates(self):
        with patch("urllib.request.OpenerDirector.open", new=fake_response(MIN_DATE_FEED)):
            contents, errors = feedergrabber("http://max.computer/index.html")
            self.assertIsNone(contents)
            self.assertEqual(2, len(errors))
            self.assertIn("Parsing methods not successful", errors[-1])
            self.assertIn("hugo page", errors[0])
