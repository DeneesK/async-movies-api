import asyncio

import aioredis

from settings import test_settings


redis_client = aioredis.from_url(f'redis://{test_settings.redis_host}')


async def main():
    while True:
        response = await redis_client.execute_command('PING')
        if response:
            break
        await asyncio.sleep(1)    


if __name__ == '__main__':
    asyncio.run(main())