from app.db.redis import *
import json
from app.router.messagerouter import flush_messages_to_db
async def flush_user_related_chats(user_number: str):
    for key in redis_client.scan_iter("chat:*:messages"):
        messages = redis_client.lrange(key, 0, -1)
        if not messages:
            continue

        flush = False
        for msg in messages:
            msg_obj = json.loads(msg)
            if msg_obj.get("sender") == user_number:
                flush = True
                break

        if flush:
            chat_id = key.split(":")[1]
            await flush_messages_to_db(chat_id)
            print(f"🧹 Flushed Redis → DB for chat_id={chat_id}")
