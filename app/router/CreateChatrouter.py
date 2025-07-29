from fastapi import Request, HTTPException, APIRouter
from app.models.models import User, Chat
from mongoengine.connection import get_db
from mongoengine.errors import DoesNotExist, ValidationError
import traceback
import logging
from app.models.models import PreChat
chat_router = APIRouter()
logger = logging.getLogger(__name__)

@chat_router.post("/addChat")
async def create_chat(request: Request):
    try:
        form = await request.json()
        print("📥 Received form:", form)

        members_dict = form.get("members", {})
        print("members_dict:",members_dict)
        member_ids = list(members_dict.values())
        print("member_ids:",member_ids)
        is_group_chat = form.get("is_group_chat", False)
        group_name = form.get("group_name")
        group_profile = form.get("group_profile") 
        other_number = members_dict.get("number")
        current_number = members_dict.get("currentUser")

        # Get other user's details (for 1-on-1)
        try:
            user = User.objects.get(phone_number=other_number)
            user_name = user.name
            user_phone = user.phone_number
            last_seen_time = user.last_seen or None
            print(f"👤 Fetched user: {user.name}")
        except (DoesNotExist, ValidationError) as e:
            user_name = "Unknown"
            user_phone = other_number or "Unknown"
            last_seen_time = "User not found"
            print(f"⚠️ Failed to fetch user info: {e}")

        # Ensure DB connection
        try:
            db = get_db()
        except Exception as e:
            print("❌ Database connection failed:", str(e))
            raise HTTPException(status_code=500, detail="Database connection failed")

        # Check for existing 1-on-1 chat
        try:
            match_chat_pipeline = [
                {
                    "$match": {
                        "is_group_chat": False,
                        "$expr": {
                            "$and": [
                                {"$eq": [{"$size": "$members"}, len(member_ids)]},
                                {"$setEquals": ["$members", member_ids]}
                            ]
                        }
                    }
                }
            ]
            stored_chat_result = list(db.chats.aggregate(match_chat_pipeline))
            if stored_chat_result:
                stored_chat = stored_chat_result[0]
                print(f"ℹ️ Chat already exists with ID: {stored_chat['_id']}")
                return {
                    "chat_id": str(stored_chat["_id"]),
                    "message": "✅ 1-on-1 Chat already exists"
                }
        except Exception as e:
            print("❌ Aggregation failed:")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Error checking for existing chat")

        # Create new chat
        try:
            new_chat = Chat(
                members=member_ids,
                is_group_chat=is_group_chat,
                group_name=group_name if is_group_chat else None,
                group_profile=group_profile if is_group_chat else None
            ).save()
            print(f"✅ Created chat: {new_chat.id}")
        except Exception as e:
            print("❌ Failed to create chat:")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Chat creation failed")

        # Add chat to current user's `prechats`
        try:
            name = members_dict.get("name")
            profile_pic = members_dict.get("profile_pic")
            user2 = User.objects.get(phone_number=current_number)

            # ✅ Create PreChat embedded document
            prechat_entry = PreChat(
                chat_id=new_chat.id,
                name=name,
                profile_pic=profile_pic
            )

            # ✅ Push it into the list
            user2.update(push__prechats=prechat_entry)

            print(f"✅ Added chat to user {user2.phone_number}'s prechats")
        except Exception as e:
            print(f"❌ Failed to update user prechats: {e}")


        return {
            "message": "✅ Chat created successfully",
            "chat_id": str(new_chat.id),
            "last_seen": last_seen_time,
            "name": user_name,
            "number": user_phone
        }

    except Exception as e:
        print("❌ Unexpected error during chat creation:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Unexpected server error")


# from fastapi import Request, HTTPException, APIRouter
# from app.models.models import User, Chat
# from mongoengine.errors import DoesNotExist
# import datetime  
# from fastapi import HTTPException
# import traceback
# import logging
# from mongoengine.connection import get_db
# chat_router = APIRouter()
# logger = logging.getLogger(__name__)
# @chat_router.post("/addChat")
# async def create_chat(request: Request):
#     form = await request.json()
#     print("📥 Received form:", form)
#     try:
#         members_dict = form.get("members", {})
#         member_ids = list(members_dict.values())
#         print("👥 Extracted member_ids:", member_ids)
#         is_group_chat = form.get("is_group_chat", False)
#         group_name = form.get("group_name")
#         group_profile = form.get("group_profile", "default_group.png")
#         other_number = members_dict.get("number")
#         current_number=members_dict.get("currentUser")
#         last_seen_time = None
#         user_name = None
#         user_phone = None       
#         try:
#             user = User.objects.get(phone_number=other_number)
#             print(user.name)
#             last_seen_time = user.last_seen if user.last_seen else None
#             user_name = user.name
#             user_phone = user.phone_number
#         except Exception as e:
#             last_seen_time = "User not found"
#             user_name = "Unknown"
#             user_phone = other_number or "Unknown"
#             print(f"⚠️ Failed to fetch user info for {other_number}: {e}")
#         try:
#             db = get_db()
#         except Exception as e:
#             print("❌ Failed to connect to database:", str(e))
#             raise HTTPException(status_code=500, detail="Database connection failed")
#         try:
#             match_chat_pipeline = [
#                 {
#                     "$match": {
#                         "is_group_chat": False,
#                         "$expr": {
#                             "$and": [
#                                 {"$eq": [{"$size": "$members"}, len(member_ids)]},
#                                 {"$setEquals": ["$members", member_ids]}
#                             ]
#                         }
#                     }
#                 }
#             ]
#             stored_chat_result = list(db.chats.aggregate(match_chat_pipeline))
#             if stored_chat_result:
#                 stored_chat = stored_chat_result[0]
#                 print(f"ℹ️ Found existing 1-on-1 chat: {stored_chat['_id']}")
#                 return {
#                     "chat_id": str(stored_chat["_id"]),
#                     "message": "✅ 1-on-1 Chat already exists"
#                 }
#         except Exception as e:
#             print("❌ Error during chat existence check via aggregation:")
#             traceback.print_exc()
#             raise HTTPException(status_code=500, detail="Error checking for existing chat")
#         try:
#             # ✅ Create new chat
#             new_chat = Chat(
#                 members=member_ids,
#                 is_group_chat=is_group_chat,
#                 group_name=group_name if is_group_chat else None,
#                 group_profile=group_profile if is_group_chat else "default_group.png"
#             ).save()
#             print(f"✅ Chat created with ID: {new_chat.id}")

#         except Exception as e:
#             print("❌ Failed to create new chat:")
#             traceback.print_exc()
#             raise HTTPException(status_code=500, detail="Chat creation failed")

#         # Replace in your addChat route
#         try:
#             current_number = members_dict.get("currentUser")
#             name = members_dict.get("name")
#             profile_pic = members_dict.get("profile_pic")

#             user2 = User.objects.get(phone_number=current_number)
#             user2.update(push__prechats={
#             "chat_id": new_chat.id,
#             "name": name,
#             "profile_pic": profile_pic
#         })

#             print("--",user2)
#             print(f"✅ Chat ID {new_chat.id} added to user {user2.phone_number}'s prechats")
#         except Exception as e:
#             print(f"❌ Failed to update user prechats: {e}")

#         print("✅ Chat created with ID:", str(new_chat.id))
#         print(user_phone)
#         return {
#             "message": "Chat created successfully",
#             "chat_id": str(new_chat.id),
#             "last_seen": last_seen_time,
#             "name": user_name,
#             "number": user_phone
#         }
#     except Exception as e:
#         print("❌ Error while creating chat:", str(e))
#         raise HTTPException(status_code=500, detail=str(e))



