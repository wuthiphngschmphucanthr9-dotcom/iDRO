# bot.py - รันทุก 5 นาทีบน GitHub Actions
# ดึงข้อความใหม่จากช่อง Discord -> หาไอดีเพลง Roblox -> ส่งเข้าเว็บฮุก
import os
import re
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = os.getenv("1564609098627031160")
WEBHOOK_URL = os.getenv("https://discord.com/api/webhooks/1566379871972884671/3lyC_ZAkYK6J-OjVZnIdJK-q3pMehV0Kb2kXgbSeI-dA78Y4XWnTP2_Y8-QMmrJdGuL-")

STATE_FILE = "last_id.txt"
API = "https://discord.com/api/v10"

URL_REGEX = re.compile(r"roblox\.com/(?:library|catalog|audio)/(\d+)", re.I)
ID_REGEX = re.compile(r"\b(\d{9,11})\b")


def check_env():
    missing = [
        name for name, val in [
            ("DISCORD_BOT_TOKEN", BOT_TOKEN),
            ("TARGET_CHANNEL_ID", CHANNEL_ID),
            ("DISCORD_WEBHOOK_URL", WEBHOOK_URL),
        ] if not val
    ]
    if missing:
        print("Error: ไม่พบค่าเหล่านี้ใน GitHub Secrets ->", ", ".join(missing))
        sys.exit(1)


def read_last_id():
    try:
        with open(STATE_FILE) as f:
            return f.read().strip() or None
    except FileNotFoundError:
        return None


def write_last_id(value):
    with open(STATE_FILE, "w") as f:
        f.write(str(value))


def fetch_messages(after=None, limit=100):
    params = {"limit": limit}
    if after:
        params["after"] = after
    r = requests.get(
        f"{API}/channels/{CHANNEL_ID}/messages",
        headers={"Authorization": f"Bot {BOT_TOKEN}"},
        params=params,
        timeout=15,
    )
    if r.status_code != 200:
        print(f"ดึงข้อความไม่สำเร็จ Status Code: {r.status_code}, Response: {r.text}")
        sys.exit(1)
    return sorted(r.json(), key=lambda m: int(m["id"]))  # เก่า -> ใหม่


def find_audio_id(text):
    m = URL_REGEX.search(text)
    if m:
        return m.group(1)
    m = ID_REGEX.search(text)
    return m.group(1) if m else None


def send_to_webhook(audio_id, author_name):
    creator_name = "ไม่ระบุข้อมูลผู้สร้าง"
    asset_name = "เพลง Roblox"
    thumbnail_url = "https://tr.rbxcdn.com/18m-1/150/150/Image/Png"

    try:
        res = requests.get(f"https://economy.roblox.com/v2/assets/{audio_id}/details", timeout=10)
        if res.status_code == 200:
            data = res.json()
            creator_name = (data.get("Creator") or {}).get("Name", "Unknown")
            asset_name = data.get("Name", asset_name)
    except Exception as e:
        print(f"ไม่สามารถดึงข้อมูลรายละเอียด: {e}")

    try:
        t = requests.get(
            f"https://thumbnails.roblox.com/v1/assets?assetIds={audio_id}&size=420x420&format=Png&isCircular=false",
            timeout=10,
        )
        if t.status_code == 200 and t.json().get("data"):
            thumbnail_url = t.json()["data"][0].get("imageUrl", thumbnail_url)
    except Exception as e:
        print(f"ไม่สามารถดึงรูปปก: {e}")

    time_now = datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%d/%m/%Y %H:%M:%S")

    payload = {
        "embeds": [{
            "title": "🎵 ตรวจพบเพลง Roblox ใหม่",
            "description": f"**ชื่อเพลง:** {asset_name}",
            "color": 5793266,
            "thumbnail": {"url": thumbnail_url},
            "fields": [
                {"name": "👤 ผู้สร้าง", "value": creator_name, "inline": True},
                {"name": "🕒 เวลาที่พบ", "value": time_now, "inline": True},
                {"name": "📌 ไอดีเพลง (มีเครื่องหมายคำพูด)", "value": f'```"{audio_id}"```'},
                {"name": "🔗 ลิงก์ต้นฉบับ", "value": f"[คลิกฟังเพลง](https://www.roblox.com/library/{audio_id})"},
            ],
            "footer": {"text": f"ผู้ส่ง: {author_name}"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }]
    }

    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการส่ง Webhook: {e}")
        return False
    if r.status_code in (200, 204):
        print(f"ส่งข้อมูลเพลง ID {audio_id} ไปยัง Webhook สำเร็จ!")
        return True
    print(f"ส่งไม่สำเร็จ Status Code: {r.status_code}, Response: {r.text}")
    return False


def main():
    check_env()
    last_id = read_last_id()

    # รันครั้งแรก: จดข้อความล่าสุดไว้เฉยๆ ไม่ส่งของเก่าย้อนหลัง
    if last_id is None:
        msgs = fetch_messages(limit=1)
        start = msgs[-1]["id"] if msgs else "0"
        write_last_id(start)
        print(f"เริ่มต้นระบบ จดข้อความล่าสุด id={start} (ครั้งต่อไปจะตรวจข้อความใหม่)")
        return

    messages = fetch_messages(after=last_id)
    print(f"พบข้อความใหม่ {len(messages)} ข้อความ")

    for msg in messages:
        author = msg.get("author", {})
        if not author.get("bot"):
            audio_id = find_audio_id(msg.get("content", ""))
            if audio_id:
                name = author.get("global_name") or author.get("username", "ไม่ทราบ")
                if not send_to_webhook(audio_id, name):
                    print("หยุดก่อน เพื่อลองส่งข้อความนี้ใหม่รอบหน้า")
                    break
        last_id = msg["id"]
        write_last_id(last_id)


if __name__ == "__main__":
    main()
