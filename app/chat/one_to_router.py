# chat_routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

router = APIRouter()
active_connections: Dict[str, WebSocket] = {}

@router.websocket("/ws/chat/{user_id}")
async def chat_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    active_connections[user_id] = websocket
    try:
        while True:
            data = await websocket.receive_json()
            receiver_id = data.get("to")
            message = data.get("message")

            if receiver_id in active_connections:
                await active_connections[receiver_id].send_json({
                    "from": user_id,
                    "message": message
                })
            else:
                await websocket.send_json({
                    "error": f"User {receiver_id} is not connected"
                })
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)
