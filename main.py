from instagrapi import Client
import time
import datetime
import os

# Instagram credentials from environment variables
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Target users (add/remove as needed)
TARGET_USERS = ["nuh.uh.avani", "manglesh.__.ks"]

MESSAGE = "WATER REMINDER!!!"

DELAY_SECONDS = 30 * 60  # 30 minutes
LOG_FILE = "reminder_log.txt"

# Active windows in UTC (24-hour format)
ACTIVE_WINDOWS = [
    (2.5, 6.5),   # 02:30 - 06:30 UTC (08:00 - 12:00 IST)
    (7.0, 17.5),  # 07:00 - 17:30 UTC (12:30 - 23:00 IST)
    (19.5, 20.5), # 19:30 - 20:30 UTC (01:00 - 02:00 IST next day)
]

def is_within_active_hours():
    """Check if current UTC time is inside active windows."""
    now = datetime.datetime.utcnow()
    current_time = now.hour + now.minute / 60
    for start, end in ACTIVE_WINDOWS:
        if start <= current_time < end:
            return True
    return False

def log_message(message: str):
    """Write logs to file and print to console."""
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    entry = f"[{timestamp}] {message}\n"
    print(entry.strip())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

def main():
    # Delete old log file at startup
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    # Initialize client with session management
    if os.path.exists("session.json"):
        cl = Client()
        cl.load_settings("session.json")
        try:
            cl.login(USERNAME, PASSWORD)
            log_message("Logged in using saved session")
        except Exception as e:
            log_message(f"Session login failed: {e}, trying fresh login...")
            cl = Client()
            cl.login(USERNAME, PASSWORD)
            cl.dump_settings("session.json")
    else:
        cl = Client()
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings("session.json")
        log_message("New session created and saved")

    # Get user IDs for all target users
    user_ids = []
    for username in TARGET_USERS:
        try:
            uid = cl.user_id_from_username(username)
            user_ids.append(uid)
            log_message(f"Resolved {username} -> {uid}")
        except Exception as e:
            log_message(f"Error resolving {username}: {e}")

    if not user_ids:
        log_message("No valid users found. Exiting.")
        return

    # Main loop
    while True:
        if is_within_active_hours():
            try:
                cl.direct_send(MESSAGE, user_ids=user_ids)
                log_message(f"Sent reminder to {len(user_ids)} users")
            except Exception as e:
                log_message(f"Error sending message: {e}")
        else:
            log_message("Inactive hours - no reminder sent")
        time.sleep(DELAY_SECONDS)

if __name__ == "__main__":
    main()
