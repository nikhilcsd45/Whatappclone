from fastapi import APIRouter, Request, HTTPException
from app.models.models import Message, User, Chat
from app.db.redis import *
from datetime import datetime
from bson import ObjectId
import json
from app.helper.flush_message_to_db import flush_messages_to_db

message_router = APIRouter()



@message_router.post("/getMessage")
async def message(request: Request):
    try:
        data = await request.json()
        print("📥 Incoming message:", data)

        sender_id = data.get("sender_id")
        receiver_id = data.get("receiver_id")
        content = data.get("content")
        chat_id = data.get("chat_id")
        timestamp = data.get("timestamp") or datetime.utcnow().isoformat()

        if not all([sender_id, receiver_id, content, chat_id]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Prepare message for Redis
        message_data = {
            "sender": sender_id,
            "receiver": receiver_id,
            "content": content,
            "timestamp": timestamp,
            "chat_id": chat_id,
            "delivered": False,
        }
        # Store in Redis temporarily
        redis_key = f"chat:{chat_id}:messages"
        redis_client.rpush(redis_key, json.dumps(message_data))
        print(f"💾 Stored in Redis → {redis_key}")

        # Auto-flush if > 50 messages
        if await redis_client.llen(redis_key) >= 50:
            await flush_messages_to_db(chat_id)

        return {"status": "✅ Message cached in Redis"}

    except Exception as e:
        print("❌ Error in message storing:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")
