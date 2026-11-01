# bot.py
import os
import re
from datetime import datetime, timezone
import requests

# อ่าน Webhook URL จาก GitHub Secrets เท่านั้น (ห้ามเขียนลงในไฟล์)
DISCORD_WEBHOOK_URL = os.getenv("https://discord.com/api/webhooks/1566370385413410829/NnfAwIbsr-5PxxXjofhgiei2Ue42VFhbIkN0GGQ55mPr072ew90HnfHV9uBUH9BrqMar")


def send_roblox_audio_notification(message_content, author_name="ระบบอัตโนมัติ GitHub Actions"):
    if not DISCORD_WEBHOOK_URL:
        print("Error: ไม่พบ DISCORD_WEBHOOK_URL (ตรวจสอบ GitHub Secrets)")
        return

    print(f"กำลังตรวจสอบข้อความ: {message_content}")
    roblox_audio_regex = r'(https?:\/\/(?:www\.)?roblox\.com\/(?:library|catalog|audio|item\.aspx\?id=)\/(\d+)\/[\w-]*)|(\b\d{9,11}\b)'
    match = re.search(roblox_audio_regex, message_content)

    if match:
        audio_id = match.group(2) or match.group(3) or re.sub(r'\D', '', message_content)
        print(f"พบ Audio ID: {audio_id}")

        creator_name = "ไม่ระบุข้อมูลผู้สร้าง"
        asset_name = "เพลง Roblox"
        thumbnail_url = "https://tr.rbxcdn.com/18m-1/150/150/Image/Png"

        try:
            res = requests.get(f'https://economy.roblox.com/v2/assets/{audio_id}/details', timeout=10)
            if res.status_code == 200:
                data = res.json()
                creator_name = data.get('Creator', {}).get('Name', 'Unknown')
                asset_name = data.get('Name', 'เพลง Roblox')
        except Exception as e:
            print(f"ไม่สามารถดึงข้อมูลรายละเอียด: {e}")

        try:
            thumb_res = requests.get(
                f'https://thumbnails.roblox.com/v1/assets?assetIds={audio_id}&size=420x420&format=Png&isCircular=false',
                timeout=10,
            )
            if thumb_res.status_code == 200:
                thumb_data = thumb_res.json()
                if thumb_data.get('data'):
                    thumbnail_url = thumb_data['data'][0].get('imageUrl', thumbnail_url)
        except Exception as e:
            print(f"ไม่สามารถดึงรูปปก: {e}")

        formatted_id_with_quotes = f'"{audio_id}"'
        time_now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        payload = {
            "embeds": [{
                "title": "🎵 ตรวจพบเพลง Roblox ใหม่ (อัตโนมัติ)",
                "description": f"**ชื่อเพลง:** {asset_name}",
                "color": 5793266,
                "thumbnail": {"url": thumbnail_url},
                "fields": [
                    {"name": "👤 ผู้สร้าง", "value": creator_name, "inline": True},
                    {"name": "🕒 เวลาที่พบ", "value": time_now, "inline": True},
                    {"name": "📌 ไอดีเพลง (มีเครื่องหมายคำพูด)", "value": f"```{formatted_id_with_quotes}```"},
                    {"name": "🔗 ลิงก์ต้นฉบับ", "value": f"[คลิกฟังเพลง](https://www.roblox.com/library/{audio_id})"},
                ],
                "footer": {"text": f"ผู้ส่ง: {author_name}"},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }]
        }

        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if response.status_code in [200, 204]:
                print(f"ส่งข้อมูลเพลง ID {audio_id} ไปยัง Webhook สำเร็จ!")
            else:
                print(f"ส่งไม่สำเร็จ Status Code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการส่ง Webhook: {e}")
    else:
        print("ไม่พบไอดีเพลง Roblox ในข้อความที่กำหนด")


if __name__ == "__main__":
    # ข้อความทดสอบ (ตอนใช้งานจริงควรเปลี่ยนเป็นแหล่งข้อมูลจริง ไม่งั้นจะส่งซ้ำทุกรอบ cron)
    sample_message = "https://www.roblox.com/library/1848354546/song"
    send_roblox_audio_notification(sample_message, "GitHub Actions Test")
