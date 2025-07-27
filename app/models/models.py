# app/models/user.py
from mongoengine import Document, StringField, BooleanField, ListField, ReferenceField, FileField, ImageField
from mongoengine.fields import ObjectIdField
from datetime import datetime
from mongoengine import DateTimeField

class User(Document):
    phone_number = StringField(required=True, unique=True)
    name = StringField()
    last_seen = DateTimeField()
    hashed_password = StringField(required=True)
    prechats = ListField(ObjectIdField())  # List of ObjectIds of other users
    profile_pic = StringField(default="default_profile.png")  # Path or URL to default pic
    prev_chat=ListField(ObjectIdField()) 
    meta = {
        'collection': 'users',
         'db_alias': 'default' # Make sure alias matches your connect()
    }
    
class Chat(Document):
    members = ListField(StringField(), required=True)  # ⬅️ Just store user IDs (as strings)
    is_group_chat = BooleanField(default=False)
    group_name = StringField(default="None")
    group_profile = StringField(default="default_group.png")
    meta = {'collection': 'chats'}
    messages_id=ListField(ObjectIdField()) 

class Message(Document):
    sender_id = ReferenceField(User, required=True)
    receiver_id = ReferenceField(User, required=True)
    content = StringField(required=True)
    last_seen = DateTimeField()
    timestamp = DateTimeField(default=datetime.utcnow)
    chat_id = ReferenceField(Chat, required=True)  # ✅ Reference to Chat document
    delivered = BooleanField(default=False)
    meta = {'collection': 'messages'}
