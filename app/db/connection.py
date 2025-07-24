from mongoengine import connect

from pymongo.server_api import ServerApi
from dotenv import load_dotenv
load_dotenv()
import os
from dotenv import load_dotenv
import os

load_dotenv()
MongoUri = os.getenv("MONGO_URI")

connect(
    db="whatappclone",       # ✅ Your actual database name
    host=MongoUri,
    alias="default"          # ✅ Use alias='default' for simplicity
)
print("Connected via MongoEngine!")
