from instagrapi import Client
import datetime
import json
import os

def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    else:
        # Fallback: use Render environment variables
        return {
            "USERNAME": os.getenv("INSTA_USER"),
            "PASSWORD": os.getenv("INSTA_PASS"),
            "TARGET_USER": os.getenv("TARGET_USER")
        }

config = load_config()
USERNAME = config["USERNAME"]
PASSWORD = config["PASSWORD"]
TARGET_USER = config["TARGET_USER"]

MESSAGE = "WATER REMINDER!!!"

def main():
    cl = Client()
    cl.login(USERNAME, PASSWORD)
    user_id = cl.user_id_from_username(TARGET_USER)
    cl.direct_send(MESSAGE, user_ids=[user_id])
    print(f"✅ Sent reminder at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} → {MESSAGE}")

if __name__ == "__main__":
    main()
