import os
import sys
import json
import time
import requests
import websocket
import threading  # Added for the heartbeat pulse
from keep_alive import keep_alive

# --- Configuration ---
status = os.getenv("status") 
custom_status = os.getenv("custom_status")
usertoken = os.getenv("token")

if not usertoken:
    print("[ERROR] Please add a token inside Secrets/Environment Variables.")
    sys.exit()

headers = {"Authorization": usertoken, "Content-Type": "application/json"}

# --- Validation ---
validate = requests.get("https://canary.discordapp.com/api/v9/users/@me", headers=headers)
if validate.status_code != 200:
    print("[ERROR] Your token might be invalid. Please check it again.")
    sys.exit()

userinfo = validate.json()
username = userinfo["username"]
discriminator = userinfo.get("discriminator", "0") # Support for new username system
userid = userinfo["id"]

def heartbeat_sender(ws, interval):
    """Keeps the connection alive by sending a pulse at the requested interval."""
    print(f"[HEARTBEAT] Thread started. Interval: {interval}ms")
    while True:
        time.sleep(interval / 1000)
        try:
            ws.send(json.dumps({"op": 1, "d": None}))
        except:
            print("[HEARTBEAT] Connection lost, stopping pulse.")
            break

def onliner(token, status):
    ws = websocket.WebSocket()
    ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
    
    # Discord sends a 'Hello' event immediately with the heartbeat interval
    hello = json.loads(ws.recv())
    heartbeat_interval = hello["d"]["heartbeat_interval"]

    # 1. Start the Heartbeat background thread
    threading.Thread(target=heartbeat_sender, args=(ws, heartbeat_interval), daemon=True).start()

    # 2. Identify (Login)
    auth = {
        "op": 2,
        "d": {
            "token": token,
            "properties": {
                "$os": "Windows 10",
                "$browser": "Google Chrome",
                "$device": "Windows",
            },
            "presence": {"status": status, "afk": False},
        },
    }
    ws.send(json.dumps(auth))

    # 3. Set Custom Status with Piano Emoji
    cstatus = {
        "op": 3,
        "d": {
            "since": 0,
            "activities": [
                {
                    "type": 4,
                    "state": custom_status,
                    "name": "Custom Status",
                    "id": "custom",
                    "emoji": {
                        "name": "🎹",
                        "id": None, # Corrected: No quotes
                        "animated": False,
                    },
                }
            ],
            "status": status,
            "afk": False,
        },
    }
    ws.send(json.dumps(cstatus))

    # 4. Keep the connection open indefinitely
    while True:
        try:
            message = ws.recv()
            if not message:
                break
        except:
            break

def run_onliner():
    os.system("clear" if os.name == "posix" else "cls")
    print(f"Logged in as {username}#{discriminator} ({userid}).")
    print("Status: Online Forever is running...")
    
    while True:
        try:
            onliner(usertoken, status)
        except Exception as e:
            print(f"[RECONNECT] Error occurred: {e}. Retrying in 10 seconds...")
            time.sleep(10)

# Start the Flask server (for keep_alive) and the onliner
keep_alive()
run_onliner()
