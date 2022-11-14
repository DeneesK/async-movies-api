from copy import deepcopy

from elasticsearch import AsyncElasticsearch, NotFoundError

from services.search import Search


class ElasticSearch(Search):
    _template = { "query":
        { "query_string":
            { "query": None } } }

    def __init__(self, es_client: AsyncElasticsearch, index_name: str):
        # index_name: 'movies'
        self.index_name = index_name
        self.elastic = es_client

    async def get_by_id(self, id_):
        return await self.elastic.get(self.index_name, id_)

    async def search(self, query, from_, page_size):
        """from_ and page_size are about pagination. """
        body = deepcopy(self._template)
        # noinspection PyTypedDict
        body['query']['query_string']['query'] = query
        if from_ is not None:
            body['from'] = from_
        if page_size is not None:
            body['size'] = page_size
        try:
            result = await self.elastic.search(index='movies', body=body)
        except NotFoundError:
            return []
        results = [f['_source'] for f in result['hits']['hits']]
        return results