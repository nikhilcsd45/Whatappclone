from fastapi import Request, HTTPException, APIRouter
from app.models.models import User, Chat
import datetime

chat_router = APIRouter()

@chat_router.post("/addChat")
async def create_chat(request: Request):
    form = await request.json()
    print("📥 Received form:", form)
    try:
        members_dict = form.get("members", {})
        member_ids = list(members_dict.values())
        print("👥 Extracted member_ids:", member_ids)

        is_group_chat = form.get("is_group_chat", False)
        group_name = form.get("group_name")
        group_profile = form.get("group_profile", "default_group.png")

        # ✅ Fetch last_seen and user info
        other_number = members_dict.get("number")
        last_seen_time = None
        user_name = None
        user_phone = None
        
        try:
            user = User.objects.get(phone_number=other_number)
            print(user.name)
            last_seen_time = user.last_seen.isoformat() if user.last_seen else None
            user_name = user.name
            user_phone = user.phone_number
        except Exception:
            last_seen_time = "User not found"
            user_name = "Unknown"
            user_phone = other_number or "Unknown"

        # ✅ Create Chat
        new_chat = Chat(
            members=member_ids,
            is_group_chat=is_group_chat,
            group_name=group_name if is_group_chat else None,
            group_profile=group_profile if is_group_chat else "default_group.png"
        ).save()

        print("✅ Chat created with ID:", str(new_chat.id))
        print(user_phone)
        return {
            "message": "Chat created successfully",
            "chat_id": str(new_chat.id),
            "last_seen": last_seen_time,
            "name": user_name,
            "number": user_phone
        }

    except Exception as e:
        print("❌ Error while creating chat:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
