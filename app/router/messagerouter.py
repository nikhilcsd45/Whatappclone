from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from bson import ObjectId
from mongoengine.connection import get_db
from app.db.redis import redis_client
import json, traceback

message_router = APIRouter()

@message_router.post("/getChat")
async def getMessage(request: Request):
    try:
        data = await request.json()
        chat_id_str = data.get("chat_id")
        current_user_number = data.get("number")

        print(f" Incoming Request: {data}")

        if not chat_id_str or not current_user_number:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "chat_id and number are required"}
            )

        try:
            chat_id = ObjectId(chat_id_str)
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "Invalid chat_id format"}
            )

        db = get_db()

        # \ud83e\uddf0 Aggregation to fetch chat and related messages
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
        print(f" Mongo Aggregated Chat: {result}")

        if not result:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "Chat not found"}
            )

        chat = result[0]
        raw_members = chat.get("members", [])
        is_group = chat.get("is_group_chat", False)

        # \ud83c\udfad Name/Profile resolution
        if is_group:
            name = chat.get("group_name", "Group")
            profile_pic = chat.get("group_profile", "")
        else:
            # Assume name and profile_pic are in 3rd and 4th index of raw_members
            name = raw_members[2] if len(raw_members) > 2 else "Unknown"
            profile_pic = raw_members[3] if len(raw_members) > 3 else ""

        # Sanitize members: keep only phone numbers
        members = [num for num in raw_members if isinstance(num, str) and num.isdigit()]

        # \ud83d\udd11 Load Redis cached messages
        redis_key = f"chat:{chat_id_str}:messages"
        print(f" Redis Key: {redis_key}")
        try:
            cached_raw = await redis_client.lrange(redis_key, 0, -1)
            print(f" Redis Cached Raw Messages: {cached_raw}")
        except Exception as e:
            print(f"Redis error: {e}")
            cached_raw = []

        cached_messages = []
        for msg in cached_raw:
            try:
                msg_dict = json.loads(msg)
                cached_messages.append(msg_dict)
            except Exception as e:
                print(f" Redis JSON parse error: {e}")

        # \ud83d\udce8 Combine all messages and sort
        all_messages = chat.get("messages", []) + cached_messages
        all_messages.sort(key=lambda x: x.get("timestamp"))

        print(f" Final Combined Messages: {all_messages}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "is_group_chat": is_group,
                "members": members,
                "name": name,
                "profile_pic": profile_pic,
                "messages": all_messages
            }
        )

    except Exception as e:
        print(f" Unhandled Exception: {traceback.format_exc()}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Internal server error", "error": str(e)}
        )
