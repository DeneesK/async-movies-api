import logging

import pydantic

from etl_models.genre import Genre
from etl_models.person import Persons
from etl_models.film import Filmwork


class ElkConverter:
    """Main class to convert datasets from Postgres format to ELK"""
    def elk_converter(self, film_works: list, persons: list, genres: list) -> pydantic.dataclasses:
        """Converts datasets to support ELK structure"""
        # TODO shrink code size by moving similar code to the external function
        logger = logging.getLogger(__name__)
        logger.debug('Starting data transform for ELK')
        # let's prepare the datastructure make it ready for the ELK
        elk_docs = []
        for film_work in film_works:
            # add all fields of film_work to corresponding ones of the ELK datastructure
            elk_doc = Filmwork(**film_work)
            try:
                elk_doc.genre = genres[film_work['id']]
            except KeyError:
                # no genre for this film_work
                pass
            try:
                if persons[film_work['id']]['director']:
                    for roles in persons[film_work['id']]['director']:
                        elk_doc.director.append(roles)
            except KeyError:
                # means there is no persons connected with current film_work, just skip
                pass
            try:
                if persons[film_work['id']]['actors']:
                    for roles in persons[film_work['id']]['actors']:
                        elk_doc.actors.append(roles)
                        elk_doc.actors_names.append(roles['name'])
            except KeyError:
                # means there is no persons connected with current film_work, just skip
                pass
            try:
                if persons[film_work['id']]['writers']:
                    for roles in persons[film_work['id']]['writers']:
                        elk_doc.writers.append(roles)
                        elk_doc.writers_names.append(roles['name'])
            except KeyError:
                # means there is no persons connected with current film_work, just skip
                pass
            elk_docs.append(elk_doc)
        logger.debug('Done transforming data for ELK')
        return elk_docs

    def elk_items_converter(self, items: list, item_type: str) -> pydantic.dataclasses:
        """Converts datasets to support ELK structure"""
        logger = logging.getLogger(__name__)
        logger.debug(f'Starting {item_type} data transform for ELK')
        # let's prepare the datastructure and make it ready for the ELK
        elk_docs = []
        if item_type == 'genre':
            elk_docs = [Genre(**item) for item in items]
        elif item_type == 'person':
            elk_docs = [Persons(**item) for item in items]
        logger.debug(f'Done transforming {item_type} data for ELK')
        return elk_docs
