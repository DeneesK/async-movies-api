import logging
from logging.handlers import RotatingFileHandler

from elasticsearch.exceptions import ConnectionError as ConErr
from aioredis.exceptions import ConnectionError


LOGGER_SETTINGS = {
    "format": "%(asctime)s - %(name)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S",
    "handlers": [RotatingFileHandler('logs.log', maxBytes=2000000, backupCount=2)],
    "level": logging.INFO
}

logging.basicConfig(**LOGGER_SETTINGS)
logger = logging.getLogger(__name__)

BACKOFF_CONFIG = {
    "exception": (ConnectionError, ConErr),
    "logger": logger,
    "max_time": 600
}
