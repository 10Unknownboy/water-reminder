from instagrapi import Client
import datetime
import json

# Load credentials from config.json
with open("config.json", "r") as f:
    config = json.load(f)

USERNAME = config["USERNAME"]
PASSWORD = config["PASSWORD"]
TARGET_USER = config["TARGET_USER"]

# Fixed message
MESSAGE = "WATER REMINDER!!!"

def main():
    cl = Client()
    cl.login(USERNAME, PASSWORD)

    user_id = cl.user_id_from_username(TARGET_USER)

    cl.direct_send(MESSAGE, user_ids=[user_id])
    print(f"✅ Sent reminder at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} → {MESSAGE}")

if __name__ == "__main__":
    main()
