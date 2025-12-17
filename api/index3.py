from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

LINE_API_URL = "https://api.line.me/v2/bot/message/push"

# 🔹 เก็บ userId ที่เคยทักมา (ตัวอย่างชั่วคราว)
LINE_USERS = set()


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
def notify_order(order_id: str):
    message = f"""
🛒 มีคำสั่งซื้อใหม่!
━━━━━━━━━━━━
📄 Order ID: {order_id}
✅ สถานะ: ยืนยันการสั่งซื้อแล้ว
━━━━━━━━━━━━
"""

    results = []
    for user_id in LINE_USERS:
        status, result = send_line_message(user_id, message)
        results.append({
            "user_id": user_id,
            "status": status
        })

    return {
        "sent_to": len(LINE_USERS),
        "results": results
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
