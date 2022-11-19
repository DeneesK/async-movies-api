import asyncio

import backoff
import aioredis
from aioredis.exceptions import ConnectionError

from settings import test_settings
from config import BACKOFF_CONFIG


redis_client = aioredis.from_url(f'redis://{test_settings.redis_host}')


@backoff.on_exception(backoff.expo, **BACKOFF_CONFIG)
async def main():
    response = await redis_client.execute_command('PING')
    if response:
        return True
    raise ConnectionError   


if __name__ == '__main__':
    asyncio.run(main())