from fastapi import APIRouter, Request, HTTPException
from app.models.models import User# Adjust if needed
from mongoengine.errors import NotUniqueError, ValidationError
import traceback

auth_router = APIRouter()

@auth_router.post("/signup")
async def signup(request: Request):
    form = await request.json()
    print("form:", form)

    try:
        user = User(
            phone_number=form["number"],
            name=form.get("name", ""),
            hashed_password=form["password"],
            prechats=[],
            profile_pic=form.get("profile_pic", "default_profile.png")
        )

        print(user.to_mongo().to_dict())
        collection = user._get_collection()
        print("Collection Name:", collection.name)
        print("Database Name:", collection.database.name)

        try:
            user.save()
        except NotUniqueError:
            raise HTTPException(status_code=409, detail="Phone number already exists")

        user_dict = user.to_mongo().to_dict()
        user_dict.pop("hashed_password", None)  # Ensure correct field name
        user_dict["_id"] = str(user_dict["_id"])

        return {
            "message": "User registered successfully",
            "user": user_dict
        }

    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=f"Validation error: {ve}")

    except KeyError as ke:
        raise HTTPException(status_code=400, detail=f"Missing field: {ke}")

    except Exception as e:
        print("Exception while saving user:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")



@auth_router.post("/login")
async def login(request: Request):
    form = await request.json()
    print("form:", form)

    phone_num = form.get("number")
    password = form.get("password")

    if not phone_num or not password:
        raise HTTPException(status_code=400, detail="Phone number and password are required")

    # ✅ Check if user exists (phone number matches)
    user = User.objects(phone_number=phone_num).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please sign up first.")

    # ✅ Check password match (you can use hashing here later)
    if user.hashed_password != password:
        raise HTTPException(status_code=401, detail="Incorrect password")

    # ✅ Return success response
    user_dict = user.to_mongo().to_dict()
    user_dict.pop("hashed_password", None)
    user_dict["_id"] = str(user_dict["_id"])

    return {
        "message": "Login successful",
        "user": user_dict
    }