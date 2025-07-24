import json
from typing import Dict
from fastapi import FastAPI, WebSocket,Request,HTTPException
from app.router.authrouter import auth_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.models.models import User
from app.db import connection
app = FastAPI()
@app.get("/")
def hello():
  return "mess"

app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, use your actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store connected clients 
connected_clients: Dict[str, WebSocket] = {}
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    number = None  # Initialize in outer scope so we can access it on disconnect

    try:
        # First message should be a JSON string like {"type":"connect", "user":"1234567899"}
        user_info_str = await websocket.receive_text()
        user_info = json.loads(user_info_str)
        number = user_info["user"]

        if number in connected_clients:
            print(f"[UPDATE] Existing user '{number}' reconnected. Updating WebSocket.")
        else:
            print(f"[NEW] New user '{number}' connected.")

        connected_clients[number] = websocket
        print(f"[CONNECTED USERS] {list(connected_clients.keys())}")

        # Listen for incoming messages
        while True:
            data = await websocket.receive_text()
            print(f"[RECEIVED] from {number}: {data}")
            await websocket.send_text(f"Echo: {data}")

    except WebSocketDisconnect:
        print(f"[DISCONNECTED] user: {number}")
        if number:
            connected_clients.pop(number, None)


@app.post("/getUser")
async def find_user(request:Request):
    form = await request.json()
    print("form:", form)

    phone_num = form.get("phone_number")
    print("phone_num:",phone_num)
    if not phone_num:
        raise HTTPException(status_code=400, detail="Phone number and password are required")

    # ✅ Check if user exists (phone number matches)
    user = User.objects(phone_number=phone_num).first()
    print("user:",user)

    if not user:
        raise HTTPException(status_code=404, detail="Number not Registered")

    # ✅ Return success response
    user_dict = user.to_mongo().to_dict()
    user_dict.pop("hashed_password", None)
    user_dict["_id"] = str(user_dict["_id"])

    return {
        "message": "user found ",
        "user": user_dict
    }

