import logging

import aioredis
import uvicorn
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api.v1 import films, persons, genres
from core import config
from core.logger import LOGGING
from db import elastic, redis

app = FastAPI(
    title="Read-only API for online cinema",
    description="Information about films, genres and people involved in the creation of the work",
    version="1.0.0",
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
)

@app.on_event('startup')
async def startup():
    redis.redis = await aioredis.from_url(f'redis://{config.REDIS_HOST}:{config.REDIS_PORT}')
    elastic.es = AsyncElasticsearch(hosts=[f'{config.ELASTIC_HOST}:{config.ELASTIC_PORT}'])


@app.on_event('shutdown')
async def shutdown():
    await redis.redis.close()
    await redis.redis.wait_closed()
    await elastic.es.close()


app.include_router(films.router, prefix='/api/v1/films', tags=['films'])
app.include_router(persons.router, prefix='/api/v1/persons', tags=['persons'])
app.include_router(genres.router, prefix='/api/v1/genres', tags=['genres'])

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        log_config=LOGGING, # To remove in updated version?
        log_level=logging.DEBUG, # To remove in updated version?
    )
