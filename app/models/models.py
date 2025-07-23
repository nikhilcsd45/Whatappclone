from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

# ✅ User schema
class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    phone: str
    name: str
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# ✅ One-to-one message schema
class Message(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    sender_id: str
    receiver_id: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# ✅ Group message schema
class GroupMessage(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    group_id: str
    sender_id: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# ✅ Group schema
class Group(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    name: str
    members: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
