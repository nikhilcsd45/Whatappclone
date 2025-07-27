from bson import ObjectId
from app.db.redis import *
import json
from app.models.models import Chat,Message
import datetime


async def flush_messages_to_db(chat_id: str):
    redis_key = f"chat:{chat_id}:messages"
    
    # 🔁 1. Get all messages from Redis
    messages = await redis_client.lrange(redis_key, 0, -1)  # async version!
    await redis_client.delete(redis_key)

    # 📦 2. Prepare list of inserted message ObjectIds
    inserted_message_ids = []

    for msg_str in messages:
        msg = json.loads(msg_str)

        # 🧾 3. Save the message to MongoDB
        saved_message = Message(
            sender_id=ObjectId(msg["sender"]),
            receiver_id=ObjectId(msg["receiver"]),
            content=msg["content"],
            timestamp=datetime.datetime.fromisoformat(msg["timestamp"]),
            chat=ObjectId(chat_id),
            delivered=msg.get("delivered", False)
        )
        saved_message.save()

        # 💾 4. Collect the inserted _id
        inserted_message_ids.append(saved_message.id)

    # 🧬 5. Update Chat with these message ids
    if inserted_message_ids:
        Chat.objects(id=ObjectId(chat_id)).update(push_all__messages_id=inserted_message_ids)

    print(f"📥 {len(inserted_message_ids)} messages flushed to MongoDB and linked to Chat ID: {chat_id}")