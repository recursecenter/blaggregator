from urllib import quote

from django.template import Library
from home.models import STREAM_CHOICES


register = Library()

@register.filter
def pagination(pages, page):
    max_items = min(7, pages)
    start = page - max_items/2
    if start < 1:
        start = 1
    end = start + max_items - 1
    if end > pages:
        end = pages
        start = end - max_items + 1
    return range(start,end + 1)

@register.filter
def stream_name(stream_id):
    return dict(STREAM_CHOICES).get(stream_id, 'Unknown')

@register.filter
def zulip_url(title, stream):
    """Return the Zulip url given the title. """

    # Some browsers zealously URI-decode the contents of window.location.hash.
    # So Zulip hides the URI-encoding by replacing '%' with '.'
    replace = lambda x: quote(x, safe='').replace('.', '%2E').replace('%', '.')
    hash_path = 'narrow/stream/%s/topic/%s' % (replace(stream), replace(title))

    return 'https://zulip.com/#%s' % hash_path
