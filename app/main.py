from fastapi import FastAPI,Request,HTTPException
from app.router.authrouter import auth_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.models.models import User
from app.db import connection ###required , do not remove
from app.router.CreateChatrouter import chat_router
from app.router.websocketRouter import websocket_router
from app.router.find_userRouter import getUser_router
from app.router.messagerouter import message_router
from app.router.getUserChats import getChats_router
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, use your actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(websocket_router)
app.include_router(getUser_router)
app.include_router(message_router)
app.include_router(getChats_router)


