import json
from typing import Dict,List
from fastapi import FastAPI, WebSocket,Request,HTTPException ,APIRouter
from app.router.authrouter import auth_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.models.models import User
from app.db import connection

websocket_router=APIRouter()

connected_clients: Dict[str, List[WebSocket]] = {}  # Now supports multiple sockets per user
@websocket_router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    number = None

    try:
        # Step 1: Identify user
        user_info_str = await websocket.receive_text()
        user_info = json.loads(user_info_str)
        number = user_info.get("user")

        if not number:
            await websocket.send_text("❌ 'user' field is required.")
            await websocket.close()
            return

        # Add websocket to list for this user
        if number in connected_clients:
            connected_clients[number].append(websocket)
            print(f"[UPDATE] Added new connection for '{number}'")
        else:
            connected_clients[number] = [websocket]
            print(f"[NEW] New user '{number}' connected")

        print(f"[CONNECTED USERS] {list(connected_clients.keys())}")
        await websocket.send_text(f"✅ Connected as {number}")

        # Step 2: Chat loop
        while True:
            raw_data = await websocket.receive_text()
            print(f"[RECEIVED] from {number}: {raw_data}")

            try:
                message_data = json.loads(raw_data)
                print("message_data:", message_data)
            except json.JSONDecodeError:
                await websocket.send_text("❌ Invalid JSON format.")
                continue

            msg_type = message_data.get("type")

            if msg_type == "message":
                inner = message_data.get("content", {})
                sender = inner.get("sender")
                receiver = str(inner.get("receiver")).strip()
                content = inner.get("content")
                chat_id = inner.get("chatId")
                timestamp = inner.get("timestamp")

                print(f"[CHAT] {sender} ➡ {receiver}: {content}")
                print(f"[LOOKUP] Trying to send to receiver: {receiver}")
                print(f"[CONNECTED CLIENTS KEYS] {list(connected_clients.keys())}")
                
                for sockets in connected_clients.values():
                    for sock in sockets:
                        await sock.send_text(json.dumps({
                                    "from": sender,
                                    "message": content,
                                    "chatId": chat_id,
                                    "timestamp": timestamp
                                }))
                    print("data broadcast")
                    
                if receiver in connected_clients:
                    
                    for sock in connected_clients[receiver]:
                        try:
                            await sock.send_text(json.dumps({
                                "from": sender,
                                "message": content,
                                "chatId": chat_id,
                                "timestamp": timestamp
                            }))
                        except Exception as e:
                            print(f"[ERROR] Failed to send to one socket: {e}")
                    print(f"[SENT] ✅ Message sent to all sockets of {receiver}")
                else:
                    await websocket.send_text("⚠️ Recipient is not online.")
                    print(f"[FAILED] ❌ {receiver} is not in connected_clients")
            else:
                await websocket.send_text("❓ Unknown message type.")

    except WebSocketDisconnect:
        print(f"[DISCONNECTED] user: {number}")
        if number and number in connected_clients:
            try:
                connected_clients[number].remove(websocket)
                print(f"[CLEANUP] Removed socket from {number}")
                if not connected_clients[number]:
                    del connected_clients[number]
                    print(f"[CLEANUP] No sockets left for {number}, removed from list")
            except ValueError:
                pass




