import os
import logging
from flask import Flask, request, jsonify
from instagrapi import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Instagram client
cl = Client()

# Load credentials from environment (set in Render dashboard)
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
TARGET_USERS = os.getenv("TARGET_USERS", "").split(",")  # comma-separated usernames

# Login session storage
SESSION_FILE = "session.json"


def login():
    """Handles login and session restore."""
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(IG_USERNAME, IG_PASSWORD)
            logger.info("Loaded session.json and logged in.")
            return True
        except Exception as e:
            logger.warning(f"Session load failed: {e}. Logging in fresh...")

    try:
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.dump_settings(SESSION_FILE)
        logger.info("Fresh login successful, session saved.")
        return True
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return False


@app.route("/")
def home():
    return "✅ Instagram Water Reminder Bot is running!"


@app.route("/send_reminder", methods=["POST"])
def send_reminder():
    """Send a reminder DM to target users."""
    if not login():
        return jsonify({"status": "error", "message": "Login failed"}), 500

    message = request.json.get("message", "💧 Time to drink water!")

    sent_to = []
    errors = []

    for username in TARGET_USERS:
        try:
            uid = cl.user_id_from_username(username)
            cl.direct_send(message, [uid])
            sent_to.append(username)
            logger.info(f"Message sent to {username}")
        except Exception as e:
            errors.append({username: str(e)})
            logger.error(f"Error sending to {username}: {e}")

    return jsonify({"status": "done", "sent": sent_to, "errors": errors})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
