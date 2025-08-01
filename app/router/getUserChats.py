from fastapi import Request, HTTPException, APIRouter
from app.models.models import User, Chat, Message
from bson import ObjectId
from mongoengine.connection import get_db
from mongoengine.errors import DoesNotExist
from fastapi import APIRouter, Request, HTTPException
from app.models.models import User
from mongoengine.errors import DoesNotExist, ValidationError
import traceback
getChats_router = APIRouter()

@getChats_router.post("/getChats")
async def getChats(request: Request):
    try:
        data = await request.json()
        number = data.get("number")

        if not number:
            raise HTTPException(status_code=400, detail="Phone number is required.")

        # Check if user exists
        user = User.objects(phone_number=number).only("prechats").first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        print("✅ User prechats:", user.prechats[0].name)  # just for debug


        pipeline = [
    {"$match": {"phone_number": number}},
    {"$unwind": "$prechats"},

    # ✅ Lookup Chat using prechats.chat_id
    {
        "$lookup": {
            "from": "chats",
            "localField": "prechats.chat_id",
            "foreignField": "_id",
            "as": "chat_info"
        }
    },
    {"$unwind": "$chat_info"},

    # ✅ Lookup latest message for the chat
    {
        "$lookup": {
            "from": "messages",
            "let": {"chat_id": "$prechats.chat_id"},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$chat_id", "$$chat_id"]}}},
                {"$sort": {"timestamp": -1}},
                {"$limit": 1}
            ],
            "as": "last_message"
        }
    },

    # ✅ Get the other member's number
    {
        "$addFields": {
            "other_member": {
                "$first": {
                    "$filter": {
                        "input": "$chat_info.members",
                        "as": "member",
                        "cond": {"$ne": ["$$member", number]}
                    }
                }
            }
        }
    },

    # ✅ Lookup other member's last_seen
    {
        "$lookup": {
            "from": "users",
            "localField": "other_member",
            "foreignField": "phone_number",
            "as": "other_user_info"
        }
    },
    {"$unwind": {"path": "$other_user_info", "preserveNullAndEmptyArrays": True}},

    # ✅ Final projection
    {
        "$project": {
            "_id": 0,
            "chat_id": {"$toString": "$prechats.chat_id"},
            "name": "$prechats.name",
            "profile_pic": "$prechats.profile_pic",
            "is_group_chat": "$chat_info.is_group_chat",
            "other_user_number": "$other_member",
            "last_seen": "$other_user_info.last_seen",
            "latest_message": {
                "$cond": {
                    "if": {"$gt": [{"$size": "$last_message"}, 0]},
                    "then": {"$arrayElemAt": ["$last_message.content", 0]},
                    "else": ""
                }
            },
            "timestamp": {
                "$cond": {
                    "if": {"$gt": [{"$size": "$last_message"}, 0]},
                    "then": {"$arrayElemAt": ["$last_message.timestamp", 0]},
                    "else": ""
                }
            }
        }
    }
]

        result = list(User.objects.aggregate(*pipeline))
        print("results:",result)
        return {"recentChats": result}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Unexpected error: {str(e)}"}

# @getChats_router.post("/getChats")
# async def getChats(request: Request):
#     try:
#         data = await request.json()
#         number = data.get("number")

#         if not number:
#             raise HTTPException(status_code=400, detail="Phone number is required.")

#         # Check if user exists
#         try:
#             user = User.objects(phone_number=number).only("prechats").first()
#             if not user:
#                 raise HTTPException(status_code=404, detail="User not found.")
#         except (DoesNotExist, ValidationError) as e:
#             raise HTTPException(status_code=404, detail="User fetch failed.") from e

#         print("✅ User prechats:", user.prechats)

#         # Define the aggregation pipeline
#         pipeline = [
#             {"$match": {"phone_number": number}},
#             {"$unwind": "$prechats"},
#             {
#                 "$lookup": {
#                     "from": "chats",
#                     "localField": "prechats.chat_id",
#                     "foreignField": "_id",
#                     "as": "chat_info"
#                 }
#             },
#             {"$unwind": "$chat_info"},
#             {
#                 "$lookup": {
#                     "from": "messages",
#                     "let": {"chat_id": "$prechats.chat_id"},
#                     "pipeline": [
#                         {"$match": {"$expr": {"$eq": ["$chat_id", "$$chat_id"]}}},
#                         {"$sort": {"timestamp": -1}},
#                         {"$limit": 1}
#                     ],
#                     "as": "last_message"
#                 }
#             },
#             {
#                 "$project": {
#                     "_id": 0,
#                     "chat_id": "$prechats.chat_id",
#                     "name": "$prechats.name",
#                     "profile_pic": "$prechats.profile_pic",
#                     "is_group_chat": "$chat_info.is_group_chat",
#                     "group_profile_pic": "$chat_info.group_profile",
#                     "latest_message": {"$arrayElemAt": ["$last_message.content", 0]},
#                     "last_seen": {"$arrayElemAt": ["$last_message.last_seen", 0]}
#                 }
#             }
#         ]
#         # Run aggregation safely
#         try:
#             result = list(User.objects.aggregate(*pipeline))
#         except Exception as e:
#             traceback.print_exc()
#             raise HTTPException(status_code=500, detail="Aggregation failed.")

#         return {"recentChats": result}

#     except Exception as e:
#         traceback.print_exc()
#         return {"error": f"Unexpected error: {str(e)}"}


 


# @getChats_router.post("/getChats")
# async def getChats(request: Request):
#     data = await request.json()
#     number = data.get("number")

#     if not number:
#         raise HTTPException(status_code=400, detail="Phone number required")
#     try:
#         user = User.objects.get(phone_number=number)
#     except User.DoesNotExist:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     chat_ids = user.prechats
#     db = get_db()

#     # Use aggregation to fetch all chat info and latest message (if any)
#     pipeline = [
#         {"$match": {"_id": {"$in": chat_ids}}},
#         {
#             "$addFields": {
#                 "last_message_id": {"$arrayElemAt": ["$messages_id", -1]}
#             }
#         },
#         {
#             "$lookup": {
#                 "from": "messages",
#                 "localField": "last_message_id",
#                 "foreignField": "_id",
#                 "as": "latest_message"
#             }
#         },
#         {
#             "$unwind": {"path": "$latest_message", "preserveNullAndEmptyArrays": True}
#         },
#         {
#             "$project": {
#                 "members": 1,
#                 "is_group_chat": 1,
#                 "group_name": 1,
#                 "group_profile": 1,
#                 "latest_message": "$latest_message.content"
#             }
#         }
#     ]

#     chat_docs = list(db.chats.aggregate(pipeline))
#     recent_chats = []
#     latest_messsage=list(db.Messages.aggerate(pipeline2))
#     for ind, chat in enumerate(chat_docs):
#         chat_dict = {
#             "chat_id": str(chat["_id"]),
#             "is_group_chat": chat["is_group_chat"],
#             "latest_message": latest_messsage[ind],
#             "name": "",
#             "profile_pic": "",
#             "group_profile_pic": "",
#             "last_seen": ""
#         }

#         if chat["is_group_chat"]:
#             chat_dict["name"] = chat.get("group_name", "Unnamed Group")
#             chat_dict["group_profile_pic"] = chat.get("group_profile", "https://res.cloudinary.com/expensetracker45/image/upload/v1753379224/ChatGPT_Image_Jul_24_2025_11_14_00_PM_dbbhzd.png")
#         else:
#             # Get other user (not the current user)
#             other_phones = [m for m in chat["members"] if m != number]
#             if other_phones:
#                 try:
#                     other_user = User.objects.get(phone_number=other_phones[0])
#                     chat_dict["name"] = other_user.name
#                     chat_dict["profile_pic"] = other_user.profile_pic
#                     chat_dict["last_seen"] = other_user.last_seen
#                 except User.DoesNotExist:
#                     chat_dict["name"] = "Unknown"
#                     chat_dict["profile_pic"] = "https://res.cloudinary.com/expensetracker45/image/upload/v1753379224/ChatGPT_Image_Jul_24_2025_11_14_00_PM_dbbhzd.png"

#         recent_chats.append(chat_dict)

#     return {"recentChats": recent_chats}




# from fastapi import Request, HTTPException, APIRouter
# from app.models.models import User, Chat
# import datetime  
# from mongoengine.errors import DoesNotExist

# getChats_router = APIRouter()
# from fastapi import Request, HTTPException, APIRouter
# from app.models.models import User, Chat, Message
# from bson import ObjectId

# getChats_router = APIRouter()

# @getChats_router.post("/getChats")
# async def getChats(request: Request):
#     data = await request.json()
#     number = data.get("number")

#     if not number:
#         raise HTTPException(status_code=400, detail="Phone number required")

#     # Step 1: Get User
#     try:
#         user = User.objects.get(phone_number=number)
        
#     except User.DoesNotExist:
#         raise HTTPException(status_code=404, detail="User not found")

#     chat_ids = user.prechats  # This is a list of ObjectId

#     # Step 2: Fetch all chats in prechats
#     chats = Chat.objects(id__in=chat_ids)

#     recent_chats = []

#     for chat in chats:
#         chat_dict = {
#             "chat_id": str(chat.id),
#             "is_group_chat": chat.is_group_chat,
#             "profile_pic": "",
#             "name": "",
#             "group_profile_pic": "",
#             "last_seen": "",
#         }

#         # Fetch latest message if exists
#         latest_msg = None
#         if chat.chat_id:
#             latest_msg_obj = Message.objects(id=chat.chat_id).first()
#             if latest_msg_obj:
#                 chat_dict["latest_message"] = latest_msg_obj.content

#         if chat.is_group_chat:
#             chat_dict["group_profile_pic"] = chat.group_profile
#             chat_dict["name"] = chat.group_name
#         else:
#             # Get the other user from members
#             other_phone = [chat.members[0]]
#             try:
#                 other_user = User.objects.get(phone_number=other_phone)
#                 chat_dict["profile_pic"] = other_user.profile_pic
#                 chat_dict["name"] = other_user.name
#                 chat_dict["last_seen"] = other_user.last_seen
#             except User.DoesNotExist:
#                 chat_dict["name"] = "Unknown"
#                 chat_dict["profile_pic"] = "default_profile.png"

#         recent_chats.append(chat_dict)

#     return {"recentChats": recent_chats}

        
        
        
        
        
    