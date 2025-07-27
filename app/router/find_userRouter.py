from fastapi import FastAPI,Request,HTTPException, APIRouter
from app.router.authrouter import auth_router
from app.models.models import User
from app.db import connection ###required

getUser_router=APIRouter()
@getUser_router.post("/getUser")
async def find_user(request:Request):
    form = await request.json()
    print("form:", form)
    phone_num = form.get("phone_number")
    print("phone_num:",phone_num)
    if not phone_num:
        raise HTTPException(status_code=400, detail="Phone number and password are required")
    user = User.objects(phone_number=phone_num).first()
    print("user:",user)
    
    if not user:
        raise HTTPException(status_code=404, detail="Number not Registered")
    user_dict = user.to_mongo().to_dict()
    user_dict.pop("hashed_password", None)
    user_dict.pop("prechats", None)
    user_dict["_id"] = str(user_dict["_id"])
    return {
        "message": "user found ",
        "user": user_dict
    }

