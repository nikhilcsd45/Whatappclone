from fastapi import APIRouter, Request, HTTPException
from app.models.models import User# Adjust if needed
from mongoengine.errors import NotUniqueError, ValidationError
import traceback

auth_router = APIRouter()
from bson import ObjectId

def serialize_mongo_document(doc):
    """Recursively convert ObjectId to str for JSON serialization."""
    if isinstance(doc, list):
        return [serialize_mongo_document(item) for item in doc]
    elif isinstance(doc, dict):
        return {
            key: serialize_mongo_document(value)
            for key, value in doc.items()
        }
    elif isinstance(doc, ObjectId):
        return str(doc)
    else:
        return doc

@auth_router.post("/signup")
async def signup(request: Request):
    try:
        form = await request.json()
        print("form:", form)

        user = User(
            phone_number=form["number"],
            name=form.get("name", ""),
            hashed_password=form["password"],
            prechats=[],
            profile_pic=form.get("profile_pic")
        )

        print(user.to_mongo().to_dict())
        collection = user._get_collection()
        print("Collection Name:", collection.name)
        print("Database Name:", collection.database.name)

        try:
            user.save()
        except NotUniqueError:
            return {
                "success": False,
                "error": "Phone number already exists",
                "code": 409
            }

        user_dict = user.to_mongo().to_dict()
        user_dict.pop("hashed_password", None)
        user_dict["_id"] = str(user_dict["_id"])
        
        user_dict = serialize_mongo_document(user.to_mongo().to_dict())
        user_dict.pop("hashed_password", None)

        return {
            "message": "User registered successfully",
            "user": user_dict
        }


    except ValidationError as ve:
        return {
            "success": False,
            "error": f"Validation error: {str(ve)}",
            "code": 422
        }

    except KeyError as ke:
        return {
            "success": False,
            "error": f"Missing field: {str(ke)}",
            "code": 400
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "code": 500
        }
        
@auth_router.post("/login")
async def login(request: Request):
    try:
        form = await request.json()
        print("📩 Incoming login data:", form)

        phone_num = form.get("number")
        password = form.get("password")

        if not phone_num or not password:
            return {
                "success": False,
                "error": "Phone number and password are required",
                "code": 400
            }

        user = User.objects(phone_number=phone_num).first()
        if not user:
            return {
                "success": False,
                "error": "User not found. Please sign up first.",
                "code": 404
            }

        if user.hashed_password != password:
            return {
                "success": False,
                "error": "Incorrect password",
                "code": 401
            }

        user_dict = user.to_mongo().to_dict()
        user_dict.pop("hashed_password", None)
        user_dict["_id"] = str(user_dict["_id"])

        user_dict = serialize_mongo_document(user.to_mongo().to_dict())
        user_dict.pop("hashed_password", None)

        return {
            "message": "Login successful",
            "user": user_dict
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "code": 500
        }

# @auth_router.post("/signup")
# async def signup(request: Request):
#     form = await request.json()
#     print("form:", form)

#     try:
#         user = User(
#             phone_number=form["number"],
#             name=form.get("name", ""),
#             hashed_password=form["password"],
#             prechats=[],
#             profile_pic=form.get("profile_pic")
#         )

#         print(user.to_mongo().to_dict())
#         collection = user._get_collection()
#         print("Collection Name:", collection.name)
#         print("Database Name:", collection.database.name)

#         try:
#             user.save()
#         except NotUniqueError:
#             return  HTTPException(status_code=409, detail="Phone number already exists")

#         user_dict = user.to_mongo().to_dict()
#         user_dict.pop("hashed_password", None)  # Ensure correct field name
#         user_dict["_id"] = str(user_dict["_id"])

#         return {
#             "message": "User registered successfully",
#             "user": user_dict
#         }

#     except ValidationError as ve:
#         raise HTTPException(status_code=422, detail=f"Validation error: {ve}")

#     except KeyError as ke:
#         raise HTTPException(status_code=400, detail=f"Missing field: {ke}")

#     except Exception as e:
#         print("Exception while saving user:", e)
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail="Internal server error")

# @auth_router.post("/login")
# async def login(request: Request):
#     try:
#         form = await request.json()
#         print("📩 Incoming login data:", form)

#         phone_num = form.get("number")
#         password = form.get("password")

#         if not phone_num or not password:
#             raise HTTPException(status_code=400, detail="Phone number and password are required")

#         # ✅ Check if user exists
#         user = User.objects(phone_number=phone_num).first()

#         if not user:
#             raise HTTPException(status_code=404, detail="User not found. Please sign up first.")

#         # ✅ Validate password (replace with hashing in production)
#         if user.hashed_password != password:
#             raise HTTPException(status_code=401, detail="Incorrect password")

#         # ✅ Prepare and sanitize response
#         user_dict = user.to_mongo().to_dict()
#         user_dict.pop("hashed_password", None)
#         user_dict["_id"] = str(user_dict["_id"])

#         return {
#             "message": "Login successful",
#             "user": user_dict
#         }

#     except HTTPException as http_exc:
#         # Pass through FastAPI's own exceptions
#         raise http_exc

#     except Exception as e:
#         # Catch unexpected errors
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")
