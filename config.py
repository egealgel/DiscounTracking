import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_IDS = [
    cid.strip()
    for cid in os.getenv("TELEGRAM_CHAT_ID", "").split(",")
    if cid.strip()
]
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
DATABASE_URL = "sqlite:///prices.db"
