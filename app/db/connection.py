import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
mongo_url = os.getenv("MONGO_URI")

client = MongoClient(mongo_url)
db = client["whatappdb"]
messages_collection = db["wptextdb"]
