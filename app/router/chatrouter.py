from fastapi import APIRouter, HTTPException, Body
from app.models.models import Chat, User
from mongoengine.errors import DoesNotExist

chat_router = APIRouter()

@chat_router.post("/create-chat")
async def create_chat(
    member_ids: list[str] = Body(...),  # list of user IDs
    is_group_chat: bool = Body(False),
    group_name: str = Body(None),
    group_profile: str = Body("default_group.png")
):
    try:
        members = [User.objects.get(id=uid) for uid in member_ids]
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="One or more users not found")
    new_chat = Chat(
        members=members,
        is_group_chat=is_group_chat,
        group_name=group_name if is_group_chat else None,
        group_profile=group_profile if is_group_chat else "default_group.png"
    ).save()

    return {
        "message": "Chat created successfully",
        "chat_id": str(new_chat.id)
    }
