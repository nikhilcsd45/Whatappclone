from fastapi import APIRouter, Request, HTTPException
from app.models.models import Message, User, Chat
from app.db.redis import *
from datetime import datetime
from bson import ObjectId
import json
from app.helper.flush_message_to_db import flush_messages_to_db
message_router = APIRouter()
from fastapi import APIRouter, Request, HTTPException
from mongoengine.connection import get_db
from bson import ObjectId
import traceback

message_router = APIRouter()
from fastapi import APIRouter, Request, HTTPException
from mongoengine.connection import get_db
from bson import ObjectId
import traceback

message_router = APIRouter()

@message_router.post("/getChat")
async def getMessage(request: Request):
    try:
        data = await request.json()
        chat_id_str = data.get("chat_id")

        if not chat_id_str:
            return {"success": False, "message": "chat_id is required"}

        try:
            chat_id = ObjectId(chat_id_str)
        except Exception:
            return {"success": False, "message": "Invalid chat_id format"}

        db = get_db()

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
                    "_id": 0,
                    "members": {
                        "$slice": ["$members", 2]
                    },
                    "name": {"$arrayElemAt": ["$members", 2]},
                    "profile_pic": {"$arrayElemAt": ["$members", 3]},
                    "is_group_chat": 1,
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

        if not result:
            return {"success": False, "message": "Chat not found"}

        return {
            "success": True,
            "message": "Chat fetched successfully",
            "data": result[0]
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

