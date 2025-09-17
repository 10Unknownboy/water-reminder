from instagrapi import Client
import time
import threading
from datetime import datetime, timezone
import os
from flask import Flask, request, redirect

# Flask app
app = Flask(__name__)

# Instagram credentials from environment
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Target users
TARGET_USERS = os.getenv("TARGET_USERS", "nuh.uh.avani,manglesh.__.ks").split(",")
MESSAGE = "WATER REMINDER!!!"

DELAY_SECONDS = 30 * 60  # 30 minutes
LOG_FILE = "reminder_log.txt"

# Active windows in UTC
ACTIVE_WINDOWS = [
    (2.5, 6.5),   # 08:00–12:00 IST
    (7.0, 17.5),  # 12:30–23:00 IST
    (19.5, 20.5), # 01:00–02:00 IST
]

logs = []   # keep recent logs
cl = Client()
user_ids = []  # global for reuse


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


def bot_loop():
    global cl, user_ids
    try:
        if os.path.exists("session.json"):
            cl.load_settings("session.json")
            cl.login(USERNAME, PASSWORD)
        else:
            cl.login(USERNAME, PASSWORD)
        cl.dump_settings("session.json")
        log_message("✅ Logged in successfully")
    except Exception as e:
        log_message(f"❌ Login failed: {e}")
        return

    # Resolve usernames once
    for username in TARGET_USERS:
        username = username.strip()
        if not username:
            continue
        try:
            uid = cl.user_id_from_username(username)
            user_ids.append(uid)
            log_message(f"Resolved {username} -> {uid}")
        except Exception as e:
            log_message(f"Error resolving {username}: {e}")

    if not user_ids:
        log_message("No valid users found. Exiting bot.")
        return

    # Loop forever
    while True:
        if is_within_active_hours():
            try:
                cl.direct_send(MESSAGE, user_ids=user_ids)
                log_message(f"📩 Sent reminder to {len(user_ids)} users")
            except Exception as e:
                log_message(f"Error sending message: {e}")
        else:
            log_message("⏸ Inactive hours - no reminder sent")
        time.sleep(DELAY_SECONDS)


# Start bot in background thread
threading.Thread(target=bot_loop, daemon=True).start()


# ---------------- WEB ROUTES ----------------

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        custom_message = request.form.get("message", "").strip()
        if custom_message:
            try:
                cl.direct_send(custom_message, user_ids=user_ids)
                log_message(f"📩 Manual reminder sent: '{custom_message}'")
                return redirect("/status")
            except Exception as e:
                log_message(f"❌ Error sending manual reminder: {e}")
                return f"<p>Error: {e}</p><a href='/'>Back</a>", 500

    # HTML form + instructions
    return """
    <h1>🚰 Water Reminder Bot</h1>
    <form method="POST">
        <textarea name="message" rows="3" cols="40" placeholder="Type your reminder..."></textarea><br>
        <button type="submit">Send Reminder</button>
    </form>
    <p>✅ Bot is running automatically.<br>
       📜 See <a href='/status'>logs</a>.</p>
    """


@app.route("/status")
def status():
    last_20 = logs[-20:] if len(logs) > 20 else logs
    return "<h2>📜 Logs (latest 20)</h2>" + "<br>".join(last_20)


@app.route("/ping")
def ping():
    return "pong", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
