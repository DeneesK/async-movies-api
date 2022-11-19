import json


def make_bulk_query(es_data, es_index, es_id_field):
    bulk_query = []
    for row in es_data:
        bulk_query.extend([
            json.dumps({'index': {'_index': es_index, '_id': row[es_id_field]}}),
            json.dumps(row)
        ])

    return bulk_query
