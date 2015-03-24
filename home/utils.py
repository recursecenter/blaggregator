from datetime import datetime
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://10.0.9.19:9200'])

def index_article(author, title, content, url, id_, timestamp=None):
    doc = {
        'author': author,
        'title': title,
        'content': content,
        'timestamp': timestamp if timestamp is not None else datetime.now(),
        'url': url
    }
    result = es.index(index="blaggragator", doc_type="post", id=id_, body=doc)
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
    results = es.search(index="blaggragator", body=body)
    return results
