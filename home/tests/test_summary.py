import feedparser
from django.test import TransactionTestCase
from home.zulip_helpers import create_summary


class ZulipSummaryTestCase(TransactionTestCase):
    def test_nested_tags(self):
        input = '<p>In this post, I want to kind of bring together the theme of curvature and the theme of affine or projective geometry. My goal is to introduce the <em>spaces of constant curvature</em> in a unified way as subspaces of Euclidean space and explore their symmetries as groups of matrices.</p>'
        expected = '\n```quote\nIn this post, I want to kind of bring together the theme of curvature and the theme of affine or projective geometry. My goal is to introduce the *spac...*\n```'
        # formatting of nested tags is preserved
        actual = create_summary(input, 150)
        self.assertEqual(expected, actual)

    def quote(self, text):
        return f"\n```quote\n{text}\n```"

    def test_plain_text_without_tags(self):
        self.assertEqual(self.quote("Just text."), create_summary("Just text."))

    def test_empty_content(self):
        self.assertEqual("", create_summary(""))

    def test_inline_html_without_paragraph(self):
        # Atom/RSS summaries often have no <p>; inline formatting is kept
        content = "Hello <b>bold</b> and <a href='http://x.com'>link</a>"
        expected = self.quote("Hello **bold** and [link](http://x.com)")
        self.assertEqual(expected, create_summary(content))

    def test_only_first_paragraph_is_used(self):
        content = "<p>First</p><p>Second</p>"
        self.assertEqual(self.quote("First"), create_summary(content))

    def test_escaped_html_is_unescaped(self):
        # Some feeds double-escape their HTML summaries
        content = "&lt;p&gt;Hello &lt;em&gt;there&lt;/em&gt;&lt;/p&gt;"
        self.assertEqual(self.quote("Hello *there*"), create_summary(content))

    def test_html_entities(self):
        content = "<p>Tom &amp; Jerry &mdash; caf&eacute;</p>"
        self.assertEqual(self.quote("Tom & Jerry — café"), create_summary(content))

    def test_unicode(self):
        self.assertEqual(
            self.quote("नमस्ते 世界 😀"), create_summary("<p>नमस्ते 世界 😀</p>")
        )

    def test_unclosed_tags(self):
        self.assertEqual(
            self.quote("Hello **bold**"), create_summary("<p>Hello <b>bold")
        )

    def test_markdown_special_chars_are_escaped(self):
        expected = self.quote(r"2 \* 3 \* 4 \_x\_")
        self.assertEqual(expected, create_summary("<p>2 * 3 * 4 _x_</p>"))

    def test_inline_code(self):
        expected = self.quote("Run `ls -la` now")
        self.assertEqual(expected, create_summary("<p>Run <code>ls -la</code> now</p>"))

    def test_line_breaks(self):
        expected = self.quote("line1  \nline2")
        self.assertEqual(expected, create_summary("<p>line1<br>line2</p>"))

    def test_list_without_paragraph(self):
        content = "<ul><li>one</li><li>two</li></ul>"
        self.assertEqual(self.quote("* one\n* two"), create_summary(content))

    def test_script_and_style_are_dropped(self):
        content = "<style>p{color:red}</style><script>alert(1)</script><p>Hi</p>"
        self.assertEqual(self.quote("Hi"), create_summary(content))

    def test_image_only_paragraph_gives_empty_summary(self):
        self.assertEqual("", create_summary("<p><img src='http://x/y.png'></p>"))

    def test_truncates_long_text_without_tags(self):
        actual = create_summary("<p>" + "x" * 600 + "</p>", 60)
        self.assertEqual(self.quote("x" * 60 + "..."), actual)

    def test_truncates_across_many_inline_tags(self):
        content = "<p>" + "<b>word</b> " * 200 + "</p>"
        actual = create_summary(content, 60)
        self.assertTrue(actual.endswith("...\n```"))
        self.assertLess(len(actual), 150)

    def test_short_content_is_not_truncated(self):
        self.assertEqual(self.quote("short"), create_summary("<p>short</p>", 60))


class FeedparserContentTestCase(TransactionTestCase):
    """Run the summary on what feedparser really gives us for different feeds."""

    RSS = (
        '<?xml version="1.0"?><rss version="2.0"><channel><title>t</title><item>'
        "<title>x</title><link>http://a/b</link><description>{}</description>"
        "</item></channel></rss>"
    )
    ATOM = (
        '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">'
        '<title>t</title><entry><title>x</title><link href="http://a/b"/>'
        "<id>1</id><updated>2020-01-01T00:00:00Z</updated>"
        "<summary{}>{}</summary></entry></feed>"
    )

    def summary(self, feed):
        return create_summary(feedparser.parse(feed).entries[0].summary)

    def quote(self, text):
        return f"\n```quote\n{text}\n```"

    def test_rss_cdata_html(self):
        feed = self.RSS.format("<![CDATA[<p>Hi <em>there</em> &amp; you</p>]]>")
        self.assertEqual(self.quote("Hi *there* & you"), self.summary(feed))

    def test_rss_escaped_html(self):
        feed = self.RSS.format("&lt;p&gt;Hi &lt;em&gt;there&lt;/em&gt; &amp;amp; you&lt;/p&gt;")
        self.assertEqual(self.quote("Hi *there* & you"), self.summary(feed))

    def test_rss_cdata_with_escaped_html(self):
        # HTML escaped twice: the text we get is still &lt;p&gt;...
        feed = self.RSS.format("<![CDATA[&lt;p&gt;Hi &lt;em&gt;there&lt;/em&gt;&lt;/p&gt;]]>")
        self.assertEqual(self.quote("Hi *there*"), self.summary(feed))

    def test_rss_html_talking_about_tags(self):
        feed = self.RSS.format("<![CDATA[<p>Use the &lt;div&gt; tag</p>]]>")
        self.assertEqual(self.quote("Use the <div> tag"), self.summary(feed))

    def test_atom_html(self):
        feed = self.ATOM.format(' type="html"', "&lt;p&gt;Hi &lt;b&gt;x&lt;/b&gt;&lt;/p&gt;")
        self.assertEqual(self.quote("Hi **x**"), self.summary(feed))

    def test_atom_xhtml(self):
        xhtml = '<div xmlns="http://www.w3.org/1999/xhtml"><p>Hi <b>x</b> &amp; y</p></div>'
        feed = self.ATOM.format(' type="xhtml"', xhtml)
        self.assertEqual(self.quote("Hi **x** & y"), self.summary(feed))

    def test_atom_plain_text(self):
        feed = self.ATOM.format("", "Tom &amp; Jerry")
        self.assertEqual(self.quote("Tom & Jerry"), self.summary(feed))

