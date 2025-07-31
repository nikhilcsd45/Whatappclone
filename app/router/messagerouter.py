from fastapi import APIRouter, Request, HTTPException
from app.models.models import Message, User, Chat
from app.db.redis import *
from datetime import datetime
from bson import ObjectId
import json
from app.helper.flush_message_to_db import flush_messages_to_db
from fastapi import APIRouter, Request, HTTPException
from mongoengine.connection import get_db
from bson import ObjectId
import traceback
message_router = APIRouter()
from fastapi import APIRouter, Request
from bson import ObjectId
import traceback
from app.db.redis import redis_client  # Redis & DB connections
from datetime import datetime
import redis.asyncio as redis

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

message_router = APIRouter()
from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId
from datetime import datetime
import json, traceback

from app.db.redis import redis_client  # ✅ Sync Redis client

message_router = APIRouter()


@message_router.post("/getChat")
async def getMessage(request: Request):
    try:
        data = await request.json()
        chat_id_str = data.get("chat_id")
        current_user_number = data.get("number")  # 🧠 Required to resolve "It's You" logic

        print(f"📥 Request to /getChat: {data}")

        if not chat_id_str or not current_user_number:
            return {"success": False, "message": "chat_id and user number are required"}

        try:
            chat_id = ObjectId(chat_id_str)
        except Exception:
            return {"success": False, "message": "Invalid chat_id format"}

        db = get_db()

        # 🧪 MongoDB Aggregation to fetch chat and messages
        pipeline = [
            {"$match": {"_id": chat_id}},
            {
                "$lookup": {
                    "from": "messages",
                    "localField": "_id",
                    "foreignField": "chat_id",
                    "as": "messages"
                }
            },
            {
                "$addFields": {
                    "messages": {
                        "$sortArray": {
                            "input": "$messages",
                            "sortBy": {"timestamp": 1}
                        }
                    }
                }
            },
            {
                "$project": {
                    "members": 1,
                    "is_group_chat": 1,
                    "group_name": 1,
                    "group_profile": 1,
                    "messages": {
                        "$map": {
                            "input": "$messages",
                            "as": "msg",
                            "in": {
                                "sender": "$$msg.sender_id",
                                "receiver": "$$msg.receiver_id",
                                "content": "$$msg.content",
                                "timestamp": "$$msg.timestamp",
                                "delivered": "$$msg.delivered"
                            }
                        }
                    }
                }
            }
        ]

        result = list(db.chats.aggregate(pipeline))
        print(f"📦 Mongo Result: {result}")

        if not result:
            return {"success": False, "message": "Chat not found"}

        chat = result[0]
        members = chat["members"]
        is_group = chat["is_group_chat"]

        # 🎭 Resolve name and profile_pic
        if is_group:
            name = chat.get("group_name", "Group")
            profile_pic = chat.get("group_profile", "")
        else:
            other_user_number = [m for m in members if m != current_user_number]
            if other_user_number:
                user_doc = db.users.find_one({"phone_number": other_user_number[0]})
                name = user_doc.get("name", "Unknown") if user_doc else "Unknown"
                profile_pic = user_doc.get("profile_pic", "")
            else:
                name = "It's You"
                profile_pic = ""

        # 🧊 Load cached messages from Redis (if any)
        redis_key = f"chat:{chat_id_str}:messages"
        print(f"🔑 Redis Key: {redis_key}")
        cached_messages = redis_client.lrange(redis_key, 0, -1)
        print(f"🧊 Redis Cached Messages: {cached_messages}")

        redis_msgs = []
        for msg in cached_messages:
            try:
                msg_dict = json.loads(msg)
                redis_msgs.append(msg_dict)
            except Exception as e:
                print(f"[❌ REDIS ERROR] Failed to load cached msg: {e}")

        # 🧪 Merge and sort all messages
        all_messages = chat.get("messages", []) + redis_msgs
        all_messages.sort(key=lambda x: x["timestamp"])

        return {
            "is_group_chat": is_group,
            "members": members,
            "name": name,
            "profile_pic": profile_pic,
            "messages": all_messages
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "success": False,
            "message": "Internal server error",
            "error": str(e)
        }

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

