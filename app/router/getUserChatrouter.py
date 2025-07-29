from fastapi import Request, APIRouter, HTTPException
from bson import ObjectId
from app.models.models import Chat
from mongoengine.connection import get_db
from datetime import datetime

getChat_router = APIRouter()

@getChat_router.post("/getChat")
async def getChat(request: Request):
    data = await request.json()
    chat_id = data.get("chat_id")
    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id is required")

    try:
        chat_object_id = ObjectId(chat_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid chat_id format")

    db = get_db()

    pipeline = [
        {"$match": {"_id": chat_object_id}},
        {
            "$lookup": {
                "from": "messages",
                "let": {"msg_ids": "$messages_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$in": ["$_id", "$$msg_ids"]}}},
                    {"$sort": {"timestamp": 1}},  # Sort inside the pipeline
                    {
                        "$project": {
                            "content": 1,
                            "timestamp": 1,
                            "last_seen": 1,
                            "sender_id": 1,
                            "receiver_id": 1
                        }
                    }
                ],
                "as": "messages"
            }
        },
        {
            "$project": {
                "members": 1,
                "is_group_chat": 1,
                "group_name": 1,
                "group_profile": 1,
                "messages": 1
            }
        }
    ]

    result = list(db.chats.aggregate(pipeline))

    if not result:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat_data = result[0]
    messages = chat_data["messages"]

    message_list = [
        {
            "content": msg.get("content"),
            "timestamp": msg.get("timestamp").isoformat() if msg.get("timestamp") else None,
            "last_seen": msg.get("last_seen").isoformat() if msg.get("last_seen") else None,
            "sender_id": str(msg["sender_id"]) if msg.get("sender_id") else None,
            "receiver_id": str(msg["receiver_id"]) if msg.get("receiver_id") else None,
            "id": str(msg["_id"]),
        }
        for msg in messages
    ]

    currentChat = {
        "members": chat_data["members"],
        "is_group_chat": chat_data["is_group_chat"],
        "group_name": chat_data["group_name"],
        "group_profile": chat_data["group_profile"],
        "latest_message": message_list[-1]["content"] if message_list else "",
        "messages": message_list
    }

    return {"currentChat": currentChat}





# from fastapi import Request, HTTPException, APIRouter
# from app.models.models import User, Chat,Message
# import datetime  
# getChat_router = APIRouter()



# @getChat_router.post("/getChat")
# async def getChat(request: Request):
#     data = await request.json()
#     chat_id = data.get("chat_id")

#     if not chat_id:
#         raise HTTPException(status_code=400, detail="chat_id is required")

#     try:
#         chat_object_id = ObjectId(chat_id)
#     except:
#         raise HTTPException(status_code=400, detail="Invalid chat_id format")

#     chat = Chat.objects(id=chat_object_id).first()
#     if not chat:
#         raise HTTPException(status_code=404, detail="Chat not found")

#     messages = Message.objects(id__in=chat.messages_id).order_by("timestamp").select_related()

#     # ✅ Use list comprehension instead of for loop
#     message_list = [
#         {
#             "id": str(msg.id),
#             "sender_id": str(msg.sender_id.id),
#             "receiver_id": str(msg.receiver_id.id),
#             "content": msg.content,
#             "timestamp": msg.timestamp.isoformat(),
#             "last_seen": msg.last_seen.isoformat() if msg.last_seen else None
#         }
#         for msg in messages
#     ]

#     currentChat = {
#         "members": chat.members,
#         "is_group_chat": chat.is_group_chat,
#         "group_name": chat.group_name,
#         "group_profile": chat.group_profile,
#         "latest_message": message_list[-1]["content"] if message_list else "",
#         "messages": message_list
#     }

#     return {"currentChat": currentChat}
