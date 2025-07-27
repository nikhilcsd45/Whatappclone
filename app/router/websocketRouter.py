import json
import asyncio
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from app.helper.flush_user_related_chats import flush_user_related_chats
websocket_router = APIRouter()

connected_clients: Dict[str, List[WebSocket]] = {}
PING_INTERVAL = 30  # seconds

@websocket_router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    number = None

    try:
        # ✅ Step 1: Identify user
        user_info_str = await websocket.receive_text()
        user_info = json.loads(user_info_str)
        number = user_info.get("user")

        if not number:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "'user' field is required."
            }))
            await websocket.close()
            return

        # ✅ Register user
        connected_clients.setdefault(number, []).append(websocket)
        print(f"[CONNECTED USERS] {list(connected_clients.keys())}")

        await websocket.send_text(json.dumps({
            "type": "status",
            "message": f"✅ Connected as {number}"
        }))

        # ✅ Receive chat messages
        async def receiver_loop():
            while True:
                raw_data = await websocket.receive_text()
                try:
                    message_data = json.loads(raw_data)
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON received."
                    }))
                    continue

                msg_type = message_data.get("type")

                if msg_type == "message":
                    inner = message_data.get("content", {})
                    sender = inner.get("sender")
                    receiver = str(inner.get("receiver")).strip()
                    content = inner.get("content")
                    chat_id = inner.get("chatId")
                    timestamp = inner.get("timestamp")

                    if not all([sender, receiver, content]):
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Missing message fields (sender, receiver, content)"
                        }))
                        continue

                    # ✅ Broadcast to receiver if online
                    if receiver in connected_clients:
                        for sock in connected_clients[receiver]:
                            await sock.send_text(json.dumps({
                                "type": "message",
                                "from": sender,
                                "message": content,
                                "chatId": chat_id,
                                "timestamp": timestamp
                            }))
                        print(f"[SENT] ✅ Message sent to all sockets of {receiver}")
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "status",
                            "message": "⚠️ Recipient is not online."
                        }))

                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "❓ Unknown message type."
                    }))

        # ✅ Ping clients to keep connection alive
        async def ping_loop():
            while True:
                await asyncio.sleep(PING_INTERVAL)
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    raise WebSocketDisconnect()

        # ✅ Run both tasks concurrently
        await asyncio.gather(receiver_loop(), ping_loop())

    except WebSocketDisconnect:
        print(f"[DISCONNECTED] user: {number}")

        if number in connected_clients:
            try:
                connected_clients[number].remove(websocket)
                if not connected_clients[number]:
                    del connected_clients[number]
                print(f"[CLEANED] Disconnected socket for {number}")
            except ValueError:
                pass

        # ✅ Flush Redis messages for any chat involving this user
        await flush_user_related_chats(number)

