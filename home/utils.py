from datetime import datetime
from HTMLParser import HTMLParser

from elasticsearch import Elasticsearch

from blaggregator.settings import ELASTICSEARCH_INDEX, ELASTICSEARCH_URL

es = Elasticsearch([ELASTICSEARCH_URL])

def index_article(author, title, content, url, id_, timestamp=None):
    doc = {
        'author': author,
        'title': title,
        'content': content,
        'timestamp': timestamp if timestamp is not None else datetime.now(),
        'url': url,
        'slug': id_,
    }

    try:
        result = es.index(index=ELASTICSEARCH_INDEX, doc_type="post", id=id_, body=doc)

    except Exception:
        result = {'created': False}

    return result


def index_post(post):
    """ Index the given post using elasticsearch. """
    user = post.blog.user
    author = '%s %s' % (user.first_name, user.last_name)
    content = _strip_tags(post.content)
    result =  index_article(
        author, post.title, content, post.url, post.slug, post.date_updated
    )
    return result


def search(query=None):
    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title", "content"]
            }
        },
        "highlight" : {
            "fields" : {
                "content" : {},
                "title": {}
                }
        }
    }

    try:
        results = es.search(index=ELASTICSEARCH_INDEX, body=body)

    except Exception:
        results = None

    return results


class _MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


def _strip_tags(html):
    s = _MLStripper()
    s.feed(html)
    return s.get_data()
