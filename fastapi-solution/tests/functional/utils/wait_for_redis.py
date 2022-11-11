import time

import aioredis


if __name__ == '__main__':
    redis_client = aioredis.from_url('redis://127.0.0.1:6379')
    while True:
        if redis_client.ping():
            break
        time.sleep(1)