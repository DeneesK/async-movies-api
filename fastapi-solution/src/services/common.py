
from db.cache import Cache
from db.search import Search

Key = str  # An id of search phrase, to look in the cache.

class DBObjectService:
    keyword = None  # must inherit

    _template = { "query":
        { "query_string":
            { "query": None } } }

    def __init__(self, cache: Cache, search: Search):
        self.cache = cache
        self.search = search