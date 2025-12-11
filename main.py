from instagrapi import Client
import time
import threading
from datetime import datetime, timezone
import os
import json
from flask import Flask, request, redirect

# Flask app
app = Flask(__name__)

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

TARGET_USERS = os.getenv("TARGET_USERS", "nuh.uh.avani,manglesh.__.ks").split(",") 
MESSAGE = "WATER REMINDER!!!"

# Reminder every 50 mins
DELAY_SECONDS = 50 * 60  

LOG_FILE = "reminder_log.txt"

# Active window in UTC (07:00–23:50 IST)
ACTIVE_WINDOWS = [
    (1.5, 18.3333)
]

logs = []
cl = Client()
user_ids = {}
username_map = {}  # uid -> username


# ===========================
# Utility Functions
# ===========================

def ensure_user_log_file(username):
    """Ensure JSON log file exists for each user."""
    os.makedirs("logs", exist_ok=True)
    filepath = f"logs/user_{username}.json"
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)
    return filepath


def append_user_log(username, entry):
    """Append an entry to a user's JSON log."""
    filepath = ensure_user_log_file(username)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    data.append(entry)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def is_within_active_hours():
    now = datetime.now(timezone.utc)
    current_time = now.hour + now.minute / 60
    for start, end in ACTIVE_WINDOWS:
        if start <= current_time < end:
            return True
    return False


def log_message(message: str):
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    entry = f"[{timestamp}] {message}"
    print(entry)
    logs.append(entry)
    if len(logs) > 200:
        logs.pop(0)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


# ===========================
# LAST ACTIVE LOGGER LOOP
# ===========================

def last_active_logger():
    """Logs last active information every 15 minutes."""
    while True:
        for uid, username in username_map.items():
            try:
                info = cl.user_info(uid)

                entry = {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "last_active_at": info.last_activity_at.isoformat() if info.last_activity_at else None,
                    "is_active": info.is_active,
                    "is_online": info.is_online
                }

                append_user_log(username, entry)
                log_message(f"Logged activity for {username}")

            except Exception as e:
                log_message(f"Error logging activity for {username}: {e}")

        time.sleep(15 * 60)  # 15 minutes


# ===========================
# BOT LOOP FOR REMINDERS
# ===========================

def bot_loop():
    global cl, user_ids, username_map

    # Login
    try:
        if os.path.exists("session.json"):
            cl.load_settings("session.json")
            cl.login(USERNAME, PASSWORD)
        else:
            cl.login(USERNAME, PASSWORD)
        cl.dump_settings("session.json")
        log_message("Logged in successfully")
    except Exception as e:
        log_message(f"Login failed: {e}")
        return

    # Resolve usernames to IDs
    for username in TARGET_USERS:
        username = username.strip()
        if not username:
            continue
        try:
            uid = cl.user_id_from_username(username)
            user_ids[uid] = username
            username_map[uid] = username
            ensure_user_log_file(username)
            log_message(f"Resolved {username} -> {uid}")
        except Exception as e:
            log_message(f"Error resolving {username}: {e}")

    if not username_map:
        log_message("No valid users found. Exiting bot.")
        return

    # Start last active logging thread
    threading.Thread(target=last_active_logger, daemon=True).start()

    # Main reminder loop
    while True:
        if is_within_active_hours():
            try:
                cl.direct_send(MESSAGE, user_ids=list(username_map.keys()))
                log_message(f"Sent reminder to {len(username_map)} users")
            except Exception as e:
                log_message(f"Error sending message: {e}")
        else:
            log_message("Inactive hours - no reminder sent")

        time.sleep(DELAY_SECONDS)


# Start bot thread
threading.Thread(target=bot_loop, daemon=True).start()


# ===========================
# WEB ROUTES
# ===========================

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        custom_message = request.form.get("message", "").strip()
        if custom_message:
            try:
                cl.direct_send(custom_message, user_ids=list(username_map.keys()))
                log_message(f"Manual reminder sent: '{custom_message}'")
                return redirect("/status")
            except Exception as e:
                log_message(f"Error sending manual reminder: {e}")
                return f"<p>Error: {e}</p><a href='/'>Back</a>", 500

    return """
    <h1>Water Reminder Bot</h1>
    <form method="POST">
        <textarea name="message" rows="3" cols="40" placeholder="Type your reminder..."></textarea><br>
        <button type="submit">Send Reminder</button>
    </form>
    <p>Bot running automatically.<br>
       See <a href='/status'>logs</a>.</p>
    """


@app.route("/status")
def status():
    last_20 = logs[-20:] if len(logs) > 20 else logs
    return "<h2>Logs (latest 20)</h2>" + "<br>".join(last_20)


@app.route("/ping")
def ping():
    return "pong", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
