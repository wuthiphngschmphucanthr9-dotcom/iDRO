import os
import re
from datetime import datetime
import discord
import requests

# ----------------------------------------------------
# วิธีที่ 1: ใส่ลิงก์ตรงๆ ในโค้ด (แทนที่ "https://discord.com/api/webhooks/1566370385413410829/NnfAwIbsr-5PxxXjofhgiei2Ue42VFhbIkN0GGQ55mPr072ew90HnfHV9uBUH9BrqMar")
# ----------------------------------------------------
DIRECT_WEBHOOK_URL = "ใส่ลิงก์เว็บฮุคของคุณที่นี่"

# ----------------------------------------------------
# วิธีที่ 2: ใช้ Environment Variable (แนะนำสำหรับ GitHub Secrets)
# ----------------------------------------------------
DISCORD_WEBHOOK_URL = DIRECT_WEBHOOK_URL if DIRECT_WEBHOOK_URL != "ใส่ลิงก์เว็บฮุคของคุณที่นี่" else os.getenv('DISCORD_WEBHOOK_URL')
TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID', '0'))
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot logged in as {client.user}!')

@client.event
async def on_message(message):
    if message.author.bot or message.channel.id != TARGET_CHANNEL_ID:
        return

    roblox_audio_regex = r'(https?:\/\/(?:www\.)?roblox\.com\/(?:library|catalog|audio)\/(\d+)\/[\w-]+)|(\b\d{9,11}\b)'
    match = re.search(roblox_audio_regex, message.content)

    if match:
        audio_id = match.group(2) or match.group(3) or re.sub(r'\D', '', message.content)
        
        creator_name = "ไม่ระบุข้อมูลผู้สร้าง"
        asset_name = "เพลง Roblox"
        thumbnail_url = "https://tr.rbxcdn.com/18m-1/150/150/Image/Png"

        try:
            res = requests.get(f'https://economy.roblox.com/v2/assets/{audio_id}/details', timeout=5)
            if res.status_code == 200:
                data = res.json()
                creator_name = data.get('Creator', {}).get('Name', 'Unknown')
                asset_name = data.get('Name', 'เพลง Roblox')
        except Exception as e:
            print(f"ไม่สามารถดึงข้อมูลรายละเอียด: {e}")

        try:
            thumb_res = requests.get(f'https://thumbnails.roblox.com/v1/assets?assetIds={audio_id}&size=420x420&format=Png&isCircular=false', timeout=5)
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
                "title": "🎵 ตรวจพบเพลง Roblox ใหม่ (พร้อมรูปปก)",
                "description": f"**ชื่อเพลง:** {asset_name}",
                "color": 5793266,
                "thumbnail": {
                    "url": thumbnail_url
                },
                "fields": [
                    {"name": "👤 ผู้สร้าง", "value": creator_name, "inline": True},
                    {"name": "🕒 เวลาที่พบ", "value": time_now, "inline": True},
                    {"name": "📌 ไอดีเพลง (มีเครื่องหมายคำพูด)", "value": f"```{formatted_id_with_quotes}```"},
                    {"name": "🔗 ลิงก์ต้นฉบับ", "value": f"[คลิกฟังเพลง](https://www.roblox.com/library/{audio_id})"}
                ],
                "footer": {
                    "text": f"ผู้ส่ง: {message.author}"
                },
                "timestamp": datetime.utcnow().isoformat()
            }]
        }

        try:
            requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
            print(f"Sent Roblox Audio ID {audio_id} to Webhook.")
        except Exception as e:
            print(f"Error sending to webhook: {e}")

client.run(DISCORD_BOT_TOKEN)
