from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WebSocketMessage(BaseModel):
    type: str  # "chat" or "group_chat"
    sender_id: str
    receiver_id: Optional[str] = None
    group_id: Optional[str] = None
    message: str
    timestamp: Optional[datetime] = None
