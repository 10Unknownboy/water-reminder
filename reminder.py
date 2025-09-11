from instagrapi import Client
import datetime
import os

USERNAME = os.getenv("INSTA_USER")
PASSWORD = os.getenv("INSTA_PASS")
TARGET_USER = os.getenv("TARGET_USER", "nuh.uh.avani")
MESSAGE = "WATER REMINDER!!!"

def main():
    cl = Client()
    cl.login(USERNAME, PASSWORD)

    user_id = cl.user_id_from_username(TARGET_USER)

    cl.direct_send(MESSAGE, user_ids=[user_id])
    print(f"✅ Sent reminder at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
