from fastapi import FastAPI
from app.router.authrouter import auth_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def hello():
  return "mess"

app.include_router(auth_router)














# templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")
# @app.get("/", response_class=HTMLResponse)
# def home(request: Request):
#     print("Rendering home page")
#     return templates.TemplateResponse("home.html", {"request": request})

# @app.post("/start-chat", response_class=HTMLResponse)
# async def start_chat(request: Request):
#     form = await request.form()
#     user_id = form.get("user_id")
#     print("Received user_id:", user_id)
#     if user_id and len(user_id) == 10 and user_id.isdigit():
#         print("Valid user_id, rendering chat page")
        
#         return templates.TemplateResponse("chat.html", {"request": request, "user_id": user_id})
#     print("Invalid user_id")
#     return templates.TemplateResponse("home.html", {"request": request, "error": "Invalid ID"})

# # WebSocket and API Handler
# chat_router = app
# active_connections = {}

# @chat_router.websocket("/ws/{user_id}")
# async def websocket_active(websocket: WebSocket, user_id: str):
#     print(f"[CONNECT] user_id={user_id}")
#     await websocket.accept()
#     active_connections[user_id] = websocket
#     print(f"[ACTIVE USERS] {list(active_connections.keys())}")
    
#     try:
#         while True:
#             data = await websocket.receive_text()
#             print(f"[RECEIVED] from {user_id}: {data}")
#             await websocket.send_text(f"{user_id}: {data}")
#             print(f"[SENT] echo to {user_id}")
#     except WebSocketDisconnect:
#         print(f"[DISCONNECT] user_id={user_id}")
#         if user_id in active_connections:
#             del active_connections[user_id]
#         print(f"[ACTIVE USERS AFTER DISCONNECT] {list(active_connections.keys())}")

# # API to check if a target user is online
# @chat_router.get("/check-user/{target_id}")
# async def check_user(target_id: str):
#     print(f"[CHECK USER] target_id={target_id}")
#     if target_id in active_connections:
#         print(f"[CHECK RESULT] {target_id} is online")
#         return {"status": "online"}
#     else:
#         print(f"[CHECK RESULT] {target_id} is offline")
#         return JSONResponse(content={"status": "offline"}, status_code=404)

