import logging
from logging.handlers import RotatingFileHandler

LOGGER_SETTINGS = {
    "format": "%(asctime)s - %(name)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S",
    "handlers": [RotatingFileHandler('./logs/db_log.log', maxBytes=2000000, backupCount=2)],
    "level": logging.INFO
}


def init_logger():
    logging.basicConfig(**LOGGER_SETTINGS)
