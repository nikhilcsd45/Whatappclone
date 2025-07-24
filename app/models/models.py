# app/models/user.py
from mongoengine import Document, StringField, BooleanField, ListField, ReferenceField, FileField, ImageField
from mongoengine.fields import ObjectIdField
from datetime import datetime
from mongoengine import DateTimeField




class User(Document):
    phone_number = StringField(required=True, unique=True)
    name = StringField()
    last_seen = BooleanField(default=True)
    hashed_password = StringField(required=True)
    prechats = ListField(ObjectIdField())  # List of ObjectIds of other users
    profile_pic = StringField(default="default_profile.png")  # Path or URL to default pic

    meta = {
        'collection': 'users',
         'db_alias': 'default' # Make sure alias matches your connect()
    }



class Message(Document):
    sender = ReferenceField(User, required=True)
    receiver = ReferenceField(User, required=True)
    content = StringField(required=True)
    last_seen = DateTimeField()
    timestamp = DateTimeField(default=datetime.utcnow)
    chat = ObjectIdField(required=True)  # Reference to Chat
    delivered=BooleanField(default=False)
    meta = {'collection': 'messages'}
class Chat(Document):
    members = ListField(StringField(), required=True)  # ⬅️ Just store user IDs (as strings)
    is_group_chat = BooleanField(default=False)
    group_name = StringField(default="None")
    group_profile = StringField(default="default_group.png")
    latest_message = StringField(default="None")  # Optional: change later if needed

    meta = {'collection': 'chats'}

