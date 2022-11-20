import os

from dotenv import load_dotenv
load_dotenv()

dsl = {
        'dbname': os.environ.get('PG_DB_NAME'),
        'user': os.environ.get('PG_USER_NAME'),
        'password': os.environ.get('PG_USER_PASSWORD'),
        'host': os.environ.get('PG_HOST'),
        'port': os.environ.get('PG_PORT'),
        'options': '-c search_path=content'}

SLEEP_TIME = 10
BATCH_SIZE = 50
ELK_BASE_URL = os.environ.get('ES_HOST')


