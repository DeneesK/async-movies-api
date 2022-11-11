import logging
import backoff

import psycopg2.extensions
import psycopg2.extras

from setting import BATCH_SIZE
from modules.states import State


class PostgresReader:
    """Main class to handle Postres operations"""
    def __init__(self):
        self.PAGE_SIZE = 500
        self.BATCH_SIZE = BATCH_SIZE
        self.QUERY_TABLE = 'film_work'
        logger = logging.getLogger('main_log')
        logger.info('Working with Postgres DB')

    @backoff.on_exception(backoff.expo, psycopg2.OperationalError, jitter=backoff.full_jitter)
    def pg_get_changes(self, pg_connector: psycopg2.extensions.connection, db_name:  str) -> list:
        """Sync current transfer state with the last modified film_work item"""
        state_dict = State().get_state()
        # get ids that were modified after the since_time timestamp
        logger = logging.getLogger(__name__)
        logger.debug(f'Fetching unsynced {db_name} ids...')
        if db_name == 'film_work':
            query = "select DISTINCT (fw.id) as item_id, fw.modified as modified " \
                    "from content.film_work fw " \
                    "left join content.genre_film_work gfw ON gfw.film_work_id = fw.id " \
                    "left join content.genre g ON g.id = gfw.genre_id " \
                    "left join content.person_film_work pfw ON pfw.film_work_id = fw.id " \
                    "left join content.person p ON p.id = pfw.person_id " \
                    f"where fw.modified > timestamp '{state_dict['last_sync']}' " \
                    f"OR g.modified > timestamp '{state_dict['last_sync']}' " \
                    f"OR p.modified > timestamp '{state_dict['last_sync']}' " \
                    f"ORDER BY modified " \
                    f"OFFSET {state_dict['query_offset']} LIMIT {self.BATCH_SIZE};"
        elif db_name in ['person', 'genre']:
            query = f"select id as item_id from {db_name} " \
                    f"where modified > timestamp '{state_dict['last_sync']}' " \
                    "ORDER BY modified " \
                    f"OFFSET {state_dict['query_offset']} LIMIT {self.BATCH_SIZE};"
        with pg_connector.cursor(cursor_factory=psycopg2.extras.DictCursor) as pg_cursor:
            pg_cursor.execute(query)
            # create resulting dict {table_name: [modified ids]}
            ids = [i['item_id'] for i in pg_cursor.fetchall()]
        logger.debug(f'Fetched unsynced {db_name} ids')
        if len(ids) == 0:
            # Means, we are done with the data transfer
            return
        return ids

    @backoff.on_exception(backoff.expo, psycopg2.OperationalError, jitter=backoff.full_jitter)
    def pg_read_data(self, pg_connector: psycopg2.extensions.connection, ids: list) -> tuple:
        """Fetch film_work items according to ids in the queue"""
        logger = logging.getLogger(__name__)
        persons = {}
        id_query = "','".join(ids)
        # fetch ELK fields corresponding film_work table
        fw_query = "SELECT fw.id as id, fw.title as title, " \
                   "fw.description as description, fw.rating as imdb_rating, " \
                   "fw.modified " \
                   "FROM content.film_work fw " \
                   f"WHERE id IN ('{id_query}')"
        with pg_connector.cursor(cursor_factory=psycopg2.extras.DictCursor) as pg_cursor:
            logger.debug('Fetching film_works from Postgres DB')
            pg_cursor.execute(fw_query)
            film_works = [fw for fw in pg_cursor.fetchall()]
            # fetch all persons connected with current film_work
            person_query = "select pfw.film_work_id as fw_id, " \
                           "JSON_AGG(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name)) " \
                           "FILTER (WHERE pfw.role = 'actor') AS actors, " \
                           "JSON_AGG(DISTINCT jsonb_build_object('id', p.id, 'name', p.full_name)) " \
                           "FILTER (WHERE pfw.role = 'writer') AS writers, " \
                           "ARRAY_AGG(DISTINCT p.full_name) " \
                           "FILTER (WHERE pfw.role = 'director') AS director " \
                           "from content.person p left outer join content.person_film_work pfw " \
                           "ON pfw.person_id = p.id " \
                           f"WHERE pfw.film_work_id IN ('{id_query}')" \
                           "GROUP BY pfw.film_work_id;"
            genre_query = "select gfw.film_work_id as fw_id, string_agg(g.name,',') genre from content.genre g " \
                          "left join content.genre_film_work gfw ON gfw.genre_id = g.id " \
                          f"WHERE gfw.film_work_id IN ('{id_query}')" \
                          f"GROUP BY fw_id;"
            logger.debug('Fetching persons and genres corresponding current film_works')
            pg_cursor.execute(person_query)
            persons.update({person['fw_id']: person for person in pg_cursor.fetchall()})
            pg_cursor.execute(genre_query)
            genres = {genre['fw_id']: ''.join(genre[1:]).split(',') for genre in pg_cursor.fetchall()}
        logger.debug('Done fetching film_works docs')
        return film_works, persons, genres

    def pg_read_secondary_data(self, pg_connector: psycopg2.extensions.connection, ids: list, db_name) -> list:
        """Fetch secondary items according to ids in the queue"""
        logger = logging.getLogger(__name__)
        id_query = "','".join(ids)
        # fetch ELK fields corresponding query table
        if db_name == 'genre':
            query = f"select id, name from {db_name} " \
                    f"where id in ('{id_query}')"
        elif db_name == 'person':
            query = f"select id, full_name from {db_name} " \
                    f"where id in ('{id_query}')"
        else:
            raise Exception('PG error while iterating secondary data')
        with pg_connector.cursor(cursor_factory=psycopg2.extras.DictCursor) as pg_cursor:
            logger.debug(f'Fetching items from {db_name} Postgres DB')
            pg_cursor.execute(query)
            items = [item for item in pg_cursor.fetchall()]
        logger.debug(f'Done fetching items from {db_name}')
        return items
