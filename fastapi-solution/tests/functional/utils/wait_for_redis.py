import time

import redis


if __name__ == '__main__':
    redis_client = redis.from_url('redis://redis:6379')
    while True:
        if redis_client.ping():
            break
        time.sleep(1)