import json
import random


def make_bulk_query(es_data, es_index, es_id_field):
    bulk_query = []
    for row in es_data:
        bulk_query.extend([
            json.dumps({'index': {'_index': es_index, '_id': row[es_id_field]}}),
            json.dumps(row)
        ])

    return bulk_query


def is_sorted(seq, key):
    return sorted(seq, key=key) == seq


def random_string(length):
    def random_char():
        return chr(random.randint(ord('a'), ord('z') + 1))
    return ''.join(random_char() for _ in range(length))
