from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv

# โหลดค่า .env
load_dotenv()

app = FastAPI()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

LINE_API_URL = "https://api.line.me/v2/bot/message/push"


def send_line_message(message: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }

    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    response = requests.post(LINE_API_URL, headers=headers, json=payload)
    return response.status_code, response.text


@app.post("/notify-order")
def notify_order(order_id: str):
    message = f"""
🛒 มีคำสั่งซื้อใหม่!
━━━━━━━━━━━━
📄 Order ID: {order_id}
✅ สถานะ: ยืนยันการสั่งซื้อแล้ว
━━━━━━━━━━━━
"""
    status, result = send_line_message(message)

    return {
        "success": status == 200,
        "status_code": status,
        "response": result
    }
    
@app.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.json()

    events = body.get("events", [])
    for event in events:
        # 📌 ตอน Add friend
        if event["type"] == "follow":
            user_id = event["source"]["userId"]
            print("NEW USER:", user_id)

            # 👉 บันทึก user_id ลง database ตรงนี้
            # save_user_to_db(user_id)

        # 📌 ตอนผู้ใช้ส่งข้อความ
        if event["type"] == "message":
            user_id = event["source"]["userId"]
            text = event["message"].get("text")
            print("MESSAGE FROM:", user_id, text)

    return {"status": "ok"}
