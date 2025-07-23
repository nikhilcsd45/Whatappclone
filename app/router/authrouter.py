from fastapi import APIRouter, Request
import os
from dotenv import load_dotenv

load_dotenv()

auth_router = APIRouter()

# Ensure default if .env is missing
frontenedroute = os.getenv("frontened_uri")

@auth_router.post(f"{frontenedroute}/signup")
async def signup(request: Request):
    form = await request.json()
    print("form:", form)
    user_id = form.get("user_id")
    return {"message": "Signup received", "user_id": user_id}
