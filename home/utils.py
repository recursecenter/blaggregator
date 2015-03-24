from datetime import datetime
from elasticsearch import Elasticsearch

from blaggregator.settings import ELASTICSEARCH_INDEX, ELASTICSEARCH_URL

es = Elasticsearch([ELASTICSEARCH_URL])

def index_article(author, title, content, url, id_, timestamp=None):
    doc = {
        'author': author,
        'title': title,
        'content': content,
        'timestamp': timestamp if timestamp is not None else datetime.now(),
        'url': url
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
    result =  index_article(
        author, post.title, post.content, post.url, post.slug, post.date_updated
    )
    return result


def search(query=None):
    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title", "content"]
            }
        }
    }

    try:
        results = es.search(index=ELASTICSEARCH_INDEX, body=body)

    except Exception:
        results = None

    return results
