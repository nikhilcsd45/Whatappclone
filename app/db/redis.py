# # app/db/redis_client.py
# import redis
# import os
# from dotenv import load_dotenv

# load_dotenv()
# REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
# redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
from redis.asyncio import Redis

# Redis connection (asyncio client)
redis_client = Redis(host='localhost', port=6379, decode_responses=True)
