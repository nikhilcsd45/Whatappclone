from fastapi import APIRouter, Request, HTTPException
from app.models.models import User  # Adjust import as per your structure
from mongoengine import NotUniqueError
import traceback

auth_router = APIRouter()
@auth_router.post("/signup")
async def signup(request: Request):
    form = await request.json()
    print("form:", form)

    try:
        print(form.get("name"))
        print(form.get("number", ""))
        print(form.get("password"))

        user = User(
            phone_number=form["number"],
            name=form.get("name", ""),
            hashed_password=form.get("password"),
            prechats=[],  # Or form.get("prechats", [])
            profile_pic=form.get("profile_pic", "default_profile.png")
        )
        print(user.to_mongo().to_dict())
        collection = user._get_collection()
        print("Collection Name:", collection.name)
        print("Database Name:", collection.database.name)
        user.save()

        # Convert MongoEngine document to dictionary
        user_dict = user.to_mongo().to_dict()

        # Remove sensitive fields
        user_dict.pop("password", None)
        user_dict["_id"] = str(user_dict["_id"])  # convert ObjectId to string

        return {
            "message": "User registered successfully",
            "user": user_dict
        }
        

    except NotUniqueError:  
        raise HTTPException(status_code=400, detail="Phone number already exists")
    except Exception as e:
        print("Exception while saving user:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

