import datetime
import logging
from contextlib import closing
from time import sleep

import psycopg2

from modules.pg_extractor import PostgresReader
from setting import dsl, BATCH_SIZE, SLEEP_TIME
from modules.elk_converter import ElkConverter
from modules.elk_writer import ElkWriter
from modules.states import State
from modules.logger import init_logger



if __name__ == '__main__':
    db_names = ['film_work', 'person', 'genre']
    query_ids = {}
    init_logger()
    logger = logging.getLogger(__name__)
    sync_time = datetime.datetime.now()
    stater = State()
    pg_reader = PostgresReader()
    elk_writer = ElkWriter()
    elk_converter = ElkConverter()
    while True:
        elk_ready = None
        elk_genres = None
        elk_persons = None
        with closing(psycopg2.connect(**dsl)) as pg_conn:
            for db in db_names:
                query_ids.update({db: PostgresReader().pg_get_changes(pg_conn, db)})
            for ids in query_ids.values():
                if ids:
                    # means there is at least one non-empty ids list
                    break
            else:
                # if we reached here we have read all ids
                state = {'last_sync': sync_time, 'query_offset': 0}
                stater.set_state(state)
                logger.info('No more entries left, waiting...')
                sleep(SLEEP_TIME)
                continue
            if query_ids['film_work']:
                film_works, persons, genres = pg_reader.pg_read_data(pg_conn, query_ids['film_work'])
                elk_ready = elk_converter.elk_converter(film_works, persons, genres)
            if query_ids['person']:
                persons_items = pg_reader.pg_read_secondary_data(pg_conn, query_ids['person'], 'person')
                elk_persons = elk_converter.elk_items_converter(persons_items, 'person')
            if query_ids['genre']:
                genres_items = pg_reader.pg_read_secondary_data(pg_conn, query_ids['genre'], 'genre')
                elk_genres = elk_converter.elk_items_converter(genres_items, 'genre')
        if elk_ready:
            elk_writer.elk_writer(elk_ready)
        if elk_persons:
            elk_writer.elk_writer(elk_persons)
        if elk_genres:
            elk_writer.elk_writer(elk_genres)
        state = stater.get_state()
        state['query_offset'] += BATCH_SIZE
        stater.set_state(state)
