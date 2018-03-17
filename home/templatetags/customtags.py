from urllib import quote

from django.template import Library

register = Library()


@register.filter
def pagination(pages, page):
    max_items = min(7, pages)
    start = page - max_items / 2
    if start < 1:
        start = 1
    end = start + max_items - 1
    if end > pages:
        end = pages
        start = end - max_items + 1
    return range(start, end + 1)


@register.filter
def zulip_url(title, stream):
    """Return the Zulip url given the title. """

    # We just replicate how Zulip creates/manages urls.
    # https://github.com/zulip/zulip/blob/33295180a918fcd420428d9aa2fb737b864cacaf/zerver/lib/notifications.py#L34

    # Some browsers zealously URI-decode the contents of window.location.hash.
    # So Zulip hides the URI-encoding by replacing '%' with '.'
    def replace(x):
        return quote(x.encode('utf-8'), safe='').replace('.', '%2E').replace('%', '.')

    hash_path = 'narrow/stream/%s/topic/%s' % (replace(stream), replace(title))

    return 'https://recurse.zulipchat.com/#%s' % hash_path
