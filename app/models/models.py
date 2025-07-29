# app/models/user.py
from mongoengine import Document, StringField, BooleanField, ListField, ReferenceField, FileField, ImageField
from mongoengine.fields import ObjectIdField
from datetime import datetime
from mongoengine import DateTimeField
from mongoengine import (
    Document, StringField, ListField,
    EmbeddedDocument, EmbeddedDocumentField, ObjectIdField
)
class PreChat(EmbeddedDocument):
    chat_id = ObjectIdField(required=True)
    name = StringField()
    profile_pic = StringField()
class User(Document):
    phone_number = StringField(required=True, unique=True)
    name = StringField()
    last_seen = DateTimeField()
    hashed_password = StringField(required=True)
    prechats = ListField(EmbeddedDocumentField(PreChat))  # List of ObjectIds of other users
    profile_pic = StringField(default="https://res.cloudinary.com/expensetracker45/image/upload/w_1000,c_fill,ar_1:1,g_auto,r_max,bo_5px_solid_red,b_rgb:262c35/v1753379224/ChatGPT_Image_Jul_24_2025_11_14_00_PM_dbbhzd.png")  # Path or URL to default pic
    meta = {
        'collection': 'users',
         'db_alias': 'default' # Make sure alias matches your connect()
    }
    
class Chat(Document):
    members = ListField(StringField(), required=True)  # ⬅️ Just store user IDs (as strings)
    is_group_chat = BooleanField(default=False)
    group_name = StringField(default="None")
    group_profile = StringField(default="https://res.cloudinary.com/expensetracker45/image/upload/w_1000,c_fill,ar_1:1,g_auto,r_max,bo_5px_solid_red,b_rgb:262c35/v1753379224/ChatGPT_Image_Jul_24_2025_11_14_00_PM_dbbhzd.png")
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
