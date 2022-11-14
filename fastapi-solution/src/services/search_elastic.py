from elasticsearch import AsyncElasticsearch, NotFoundError

from services.search import Search


class ElasticSearch(Search):
    def __init__(self, es_client: AsyncElasticsearch, index_name: str):
        # index_name: 'movies'
        self.index_name = index_name
        self.elastic = es_client

    async def get_by_id(self, id_):
        return await self.elastic.get(self.index_name, id_)

    async def search(self, query, from_, page_size,
                     sort_fields:list|None=None,
                     filter_items:list|None=None):
        """from_ and page_size are about pagination.
        :param sort_fields:
        :param filter_items:
        """
        if filter_items is None:
            body = { "query": { "query_string": { "query": query}}}
            body['query']['query_string']['query'] = query
        else:
            body = {"query": {'bool': {'must': {"match": {"name": {"query": query}}}}}}
            body["query"]["bool"]["filter"] = [{'term': {"name": filter_item}} for filter_item in filter_items]
        if sort_fields:
            # noinspection PyTypeChecker
            body["sort"] = [{sort_field: 'asc'} for sort_field in sort_fields]
        if from_ is not None:
            body['from'] = from_
        if page_size is not None:
            body['size'] = page_size
        try:
            result = await self.elastic.search(index=self.index_name, body=body)
        except NotFoundError:
            return []
        results = [f['_source'] for f in result['hits']['hits']]
        return results