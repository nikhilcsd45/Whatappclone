from fastapi import APIRouter, Request
import os
from dotenv import load_dotenv
from app.db.connection import client  # You are importing 'client' correctly
load_dotenv()

auth_router = APIRouter()

frontenedroute = os.getenv("frontened_uri")

@auth_router.post("/signup")
async def signup(request: Request):
    form = await request.json()
    print("form:", form)
    db = client["whatappclone"]["users"]     
    result = db.insert_one(form) 
    inserted_id = str(result.inserted_id)      

    return {
        "message": "Signup received",
        "inserted_id": inserted_id
    }
