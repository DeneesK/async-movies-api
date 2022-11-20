import logging

import backoff
import pydantic
import elasticsearch
from elasticsearch.helpers import bulk

from etl_models.film import Filmwork
from etl_models.genre import Genre
from etl_models.person import Persons

from etl.es_schemes import filmwork_index_body, genre_index_body, person_index_body
from settings import ELK_BASE_URL


class ElkWriter:
    def __int__(self):
        logger = logging.getLogger('main_log')
        logger.info('Working with ELK..')

    def check_index(self, elk_connection: elasticsearch.Elasticsearch):
        """Ensure ELK index exists. If not, create it"""
        logger = logging.getLogger(__name__)
        logger.debug('Ensuring movie index existence...')
        if not elk_connection.indices.exists('movies'):
            elk_connection.indices.create('movies', filmwork_index_body)
        if not elk_connection.indices.exists('persons'):
            elk_connection.indices.create('persons', person_index_body)
        if not elk_connection.indices.exists('genres'):
            elk_connection.indices.create('genres', genre_index_body)

    def elk_iterator(self, dataset: pydantic.dataclasses, data_type: str) -> pydantic.dataclasses:
        """Prepare ELK data chunks to write to the Elastic DB"""
        if data_type == 'film_work':
            for data_sample in dataset:
                yield {
                    '_index': 'movies',
                    '_id': data_sample.id,
                    'id': data_sample.id,
                    'imdb_rating': data_sample.imdb_rating,
                    'genre': data_sample.genre,
                    'title': data_sample.title,
                    'description': data_sample.description,
                    'director': data_sample.director,
                    'actors_names': data_sample.actors_names,
                    'writers_names': data_sample.writers_names,
                    'actors': data_sample.actors,
                    'writers': data_sample.writers,
                }
        elif data_type == 'genre':
            for data_sample in dataset:
                yield {
                          '_index': 'genres',
                          '_id': data_sample.id,
                          'id': data_sample.id,
                          'name': data_sample.name,
                          'description': data_sample.description,
                }
        elif data_type == 'person':
            for data_sample in dataset:
                yield {
                          '_index': 'persons',
                          '_id': data_sample.id,
                          'id': data_sample.id,
                          'name': data_sample.full_name,
                }

    @backoff.on_exception(backoff.expo, elasticsearch.ConnectionError, jitter=backoff.full_jitter)
    def elk_writer(self, data: list):
        """Write prepared data chunks to the Elastic DB"""
        logger = logging.getLogger(__name__)
        logger.info('Writing data to ELK')
        base_url = ELK_BASE_URL
        try:
            es = elasticsearch.Elasticsearch(base_url)
        except elasticsearch.ConnectionError:
            logger.warning('Error while connecting to ELK')
        else:
            # ensure that index exists
            self.check_index(es)
            if isinstance(data[0], Filmwork):
                bulk(es, self.elk_iterator(data, 'film_work'))
            elif isinstance(data[0], Genre):
                bulk(es, self.elk_iterator(data, 'genre'))
            elif isinstance(data[0], Persons):
                bulk(es, self.elk_iterator(data, 'person'))
            logger.info('Done writing data to ELK')
