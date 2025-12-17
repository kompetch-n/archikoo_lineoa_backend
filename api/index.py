from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

app = FastAPI()

# ✅ CORS CONFIG
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",          # dev
        "https://archikoo.vercel.app",    # prod (ถ้ามี)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

LINE_API_URL = "https://api.line.me/v2/bot/message/push"

# 🔹 เก็บ userId ที่เคยทักมา (ตัวอย่างชั่วคราว)
# LINE_USERS = set()

class NotifyOrderRequest(BaseModel):
    order_id: str
    user_id: str

def send_line_message(user_id: str, message: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }

    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    response = requests.post(LINE_API_URL, headers=headers, json=payload)
    return response.status_code, response.text


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/notify-order")
def notify_order(data: NotifyOrderRequest):
    message = f"""
🛒 มีคำสั่งซื้อใหม่!
━━━━━━━━━━━━
📄 Order ID: {data.order_id}
✅ สถานะ: ยืนยันการสั่งซื้อแล้ว
━━━━━━━━━━━━
"""

    status, result = send_line_message(data.user_id, message)

    return {
        "success": status == 200,
        "user_id": data.user_id,
        "status_code": status,
        "response": result
    }

@app.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.json()
    events = body.get("events", [])

    for event in events:
        user_id = event["source"]["userId"]

        # ✅ ตอน Add friend
        if event["type"] == "follow":
            LINE_USERS.add(user_id)
            print("NEW FOLLOWER:", user_id)

        # ✅ ตอนส่งข้อความ
        if event["type"] == "message":
            text = event["message"].get("text")
            LINE_USERS.add(user_id)
            print("MESSAGE FROM:", user_id, text)

            # (optional) ตอบกลับ
            send_line_message(user_id, "รับข้อความแล้วครับ 🙏")

    return {"status": "ok"}

@app.get("/line/users")
def get_line_users():
    return {
        "count": len(LINE_USERS),
        "users": list(LINE_USERS)
    }
