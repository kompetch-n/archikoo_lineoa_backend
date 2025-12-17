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
LINE_USERS = set()

class NotifyOrderRequest(BaseModel):
    user_id: str
    name: str
    product_label: str
    quantity: int
    phone: str
    address: str
    note: str | None = None
    image_url: str

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
🛒 คำสั่งซื้อใหม่ (ยืนยันแล้ว)
━━━━━━━━━━━━
👤 ชื่อ: {data.name}
📦 สินค้า: {data.product_label}
🔢 จำนวน: {data.quantity}
📞 โทร: {data.phone}

🏠 ที่อยู่จัดส่ง
{data.address}
"""

    if data.note:
        message += f"\n📝 หมายเหตุ:\n{data.note}\n"

    message += f"""
━━━━━━━━━━━━
📷 สลิปชำระเงิน:
{data.image_url}
"""

    status, result = send_line_message(data.user_id, message)

    return {
        "success": status == 200,
        "line_status": status,
        "line_response": result
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
