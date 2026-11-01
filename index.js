// index.js
const { Client, GatewayIntentBits } = require('discord.js');
const axios = require('axios');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
});

const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL;
const TARGET_CHANNEL_ID = process.env.TARGET_CHANNEL_ID;

client.once('ready', () => {
    console.log(`Bot logged in as ${client.user.tag}!`);
});

client.on('messageCreate', async (message) => {
    if (message.author.bot || message.channel.id !== TARGET_CHANNEL_ID) return;

    const robloxAudioRegex = /(https?:\/\/(?:www\.)?roblox\.com\/(?:library|catalog|audio)\/(\d+)\/[\w-]+)|(\b\d{9,11}\b)/g;
    const match = message.content.match(robloxAudioRegex);

    if (match) {
        const audioId = match[2] || match[3] || message.content.replace(/\D/g, '');
        
        let creatorName = "ไม่ระบุข้อมูลผู้สร้าง";
        let assetName = "เพลง Roblox";
        let thumbnailUrl = "https://tr.rbxcdn.com/18m-1/150/150/Image/Png"; // ค่าสำรองถ้าดึงรูปไม่ได้

        // ดึงข้อมูลรายละเอียดเพลงจาก Roblox API
        try {
            const res = await axios.get(`https://economy.roblox.com/v2/assets/${audioId}/details`);
            if (res.data) {
                creatorName = res.data.Creator ? res.data.Creator.Name : "Unknown";
                assetName = res.data.Name || "เพลง Roblox";
            }
        } catch (e) {
            console.log("ไม่สามารถดึงข้อมูลรายละเอียดจาก API ได้");
        }

        // ดึงรูปไอคอน/ปกจาก Thumbnail API
        try {
            const thumbRes = await axios.get(`https://thumbnails.roblox.com/v1/assets?assetIds=${audioId}&size=420x420&format=Png&isCircular=false`);
            if (thumbRes.data && thumbRes.data.data && thumbRes.data.data.length > 0) {
                thumbnailUrl = thumbRes.data.data[0].imageUrl || thumbnailUrl;
            }
        } catch (e) {
            console.log("ไม่สามารถดึงรูปปกจาก Thumbnail API ได้");
        }

        const formattedIdWithQuotes = `"${audioId}"`;
        const timeNow = new Date().toLocaleString('th-TH', { timeZone: 'Asia/Bangkok' });

        const payload = {
            embeds: [{
                title: "🎵 ตรวจพบเพลง Roblox ใหม่ (พร้อมรูปปก)",
                description: `**ชื่อเพลง:** ${assetName}`,
                color: 0x5865F2,
                thumbnail: {
                    url: thumbnailUrl
                },
                fields: [
                    { name: "👤 ผู้สร้าง", value: creatorName, inline: true },
                    { name: "🕒 เวลาที่พบ", value: timeNow, inline: true },
                    { name: "📌 ไอดีเพลง (มีเครื่องหมายคำพูด)", value: `\`\`\`${formattedIdWithQuotes}\`\`\`` },
                    { name: "🔗 ลิงก์ต้นฉบับ", value: `[คลิกฟังเพลง](https://www.roblox.com/library/${audioId})` }
                ],
                footer: {
                    text: `ผู้ส่ง: ${message.author.tag}`
                },
                timestamp: new Date()
            }]
        };

        try {
            await axios.post(DISCORD_WEBHOOK_URL, payload);
            console.log(`Sent Roblox Audio ID ${audioId} with thumbnail and metadata to Webhook.`);
        } catch (error) {
            console.error('Error sending to webhook:', error);
        }
    }
});

client.login(process.env.DISCORD_BOT_TOKEN);
