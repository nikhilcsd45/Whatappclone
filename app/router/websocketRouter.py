from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from app.models.models import User, Chat, Message
from app.db.redis import redis_client
from bson import ObjectId
from datetime import datetime
import json, traceback, asyncio

websocket_router = APIRouter()
PING_INTERVAL = 20
connected_clients = {}

# ✅ Flush cached Redis messages to DB
async def flush_messages_to_db(chat_id: str):
    try:
        redis_key = f"chat:{chat_id}:messages"
        messages = await redis_client.lrange(redis_key, 0, -1)

        if not messages:
            print(f"ℹ️ No messages to flush for chat {chat_id}")
            return

        await redis_client.delete(redis_key)
        print(f"🧹 Deleted Redis key after flush: {redis_key}")

        for raw_msg in messages:
            try:
                msg = json.loads(raw_msg)
                sender_obj = User.objects(phone_number=msg["sender"]).first()
                receiver_obj = User.objects(phone_number=msg["receiver"]).first()
                chat_obj = Chat.objects(id=ObjectId(chat_id)).first()

                if not (sender_obj and receiver_obj and chat_obj):
                    print(f"⚠️ Invalid user/chat reference. Skipping message: {msg}")
                    continue

                Message(
                    sender_id=sender_obj,
                    receiver_id=receiver_obj,
                    content=msg["content"],
                    chat_id=chat_obj,
                    timestamp=datetime.fromisoformat(msg["timestamp"]),
                    delivered=True
                ).save()
                print(f"✅ Saved message to DB: {msg['content']}")

            except Exception as e:
                print("❌ Error saving message to DB:", e)
                traceback.print_exc()

        print(f"📦 Flushed {len(messages)} messages from Redis to MongoDB for chat {chat_id}")

    except Exception as e:
        print("❌ Error during flush_messages_to_db:", e)
        traceback.print_exc()


# ✅ WebSocket Chat Handler
@websocket_router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    number = None

    try:
        user_info_str = await websocket.receive_text()
        user_info = json.loads(user_info_str)
        number = user_info.get("user")

        if not number:
            await websocket.send_text(json.dumps({
                "type": "error", "message": "'user' field is required."
            }))
            await websocket.close()
            return

        connected_clients.setdefault(number, []).append(websocket)
        print(f"[CONNECTED] ✅ User connected: {number}")
        await websocket.send_text(json.dumps({
            "type": "status", "message": f"✅ Connected as {number}"
        }))

        # 📥 Message Receiver Loop
        async def receiver_loop():
            while True:
                try:
                    raw_data = await websocket.receive_text()
                    message_data = json.loads(raw_data)

                    if message_data.get("type") != "message":
                        await websocket.send_text(json.dumps({
                            "type": "error", "message": "❓ Unknown message type."
                        }))
                        continue

                    inner = message_data.get("content", {})
                    sender = inner.get("sender")
                    receiver = str(inner.get("receiver")).strip()
                    content = inner.get("content")
                    chat_id = inner.get("chatId")
                    timestamp = inner.get("timestamp")

                    if not all([sender, receiver, content, chat_id, timestamp]):
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "❌ Missing sender, receiver, content, chatId, or timestamp"
                        }))
                        continue

                    # 📤 Send message to receiver if online
                    if receiver in connected_clients:
                        for sock in connected_clients[receiver]:
                            await sock.send_text(json.dumps({
                                "type": "message",
                                "from": sender,
                                "message": content,
                                "chatId": chat_id,
                                "timestamp": timestamp
                            }))
                        print(f"[SENT] 📤 Message delivered to {receiver}")
                    else:
                        print(f"[OFFLINE] ⚠️ Receiver {receiver} not connected")

                    # 💾 Cache to Redis
                    redis_key = f"chat:{chat_id}:messages"
                    await redis_client.rpush(redis_key, json.dumps(inner))
                    print(f"📥 Cached message to Redis: {content}")

                    # 🚨 Auto-flush if ≥ 50
                    if await redis_client.llen(redis_key) >= 50:
                        print(f"🚨 Redis buffer full (≥50) for chat {chat_id}, flushing to DB")
                        await flush_messages_to_db(chat_id)

                except Exception as e:
                    print("❌ [RECEIVER ERROR] Error handling message:", e)
                    traceback.print_exc()
                    await websocket.send_text(json.dumps({
                        "type": "error", "message": "❌ Message processing failed"
                    }))

        # 🔁 Ping loop to keep connection alive
        async def ping_loop():
            while True:
                await asyncio.sleep(PING_INTERVAL)
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except:
                    raise WebSocketDisconnect()

        await asyncio.gather(receiver_loop(), ping_loop())

    except WebSocketDisconnect:
        print(f"[DISCONNECTED] 🔌 User {number} disconnected")

        if number and number in connected_clients:
            try:
                connected_clients[number].remove(websocket)
                if not connected_clients[number]:
                    del connected_clients[number]
                print(f"[CLEANUP] ✅ Removed socket for {number}")
            except ValueError:
                pass

        # 🧹 Flush messages from all chats user was in
        try:
            if number:
                user = User.objects(phone_number=number).first()
                if user:
                    chat_objs = Chat.objects(members=number)
                    for chat in chat_objs:
                        await flush_messages_to_db(str(chat.id))
        except Exception as e:
            print("❌ Error during disconnect flush:", e)
            traceback.print_exc()

    except Exception as e:
        print("❌ WebSocket main error:", e)
        traceback.print_exc()
        await websocket.close()


