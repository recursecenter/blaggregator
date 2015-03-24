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
    result = es.index(index=ELASTICSEARCH_INDEX, doc_type="post", id=id_, body=doc)
    return result['created']


def search(query=None):
    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title", "content"]
            }
        }
    }
    results = es.search(index=ELASTICSEARCH_URL, body=body)
    return results
