import re
from urllib.parse import quote

from django.template import Library, Node

register = Library()


@register.tag(name="stripnewlines")
def strip_newlines(parser, token):
    nodelist = parser.parse(("endstripnewlines",))
    parser.delete_first_token()
    return StripNewlinesNode(nodelist)


class StripNewlinesNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        return re.sub(r"\s+", " ", output.strip())


@register.filter
def zulip_url(title, stream):
    """Return the Zulip url given the title."""

    # We just replicate how Zulip creates/manages urls.
    # https://github.com/zulip/zulip/blob/33295180a918fcd420428d9aa2fb737b864cacaf/zerver/lib/notifications.py#L34
    # Some browsers zealously URI-decode the contents of window.location.hash.
    # So Zulip hides the URI-encoding by replacing '%' with '.'
    def replace(x):
        return quote(x.encode("utf-8"), safe="").replace(".", "%2E").replace("%", ".")

    if len(title) > 60:
        title = title[:57] + "..."
    hash_path = "narrow/stream/%s/topic/%s" % (replace(stream), replace(title))
    return "https://recurse.zulipchat.com/#%s" % hash_path


@register.filter
def filter_control_chars(text):
    """Filter control characters from a given text."""
    return re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]", "", text)
