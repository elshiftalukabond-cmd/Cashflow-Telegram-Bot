import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

def get_env_int(key, default=None):
    """ .env dan qiymatni xavfsiz Integer qilib olish """
    try:
        return int(os.getenv(key))
    except (ValueError, TypeError):
        return os.getenv(key) if os.getenv(key) else default

CHANNEL_ID = get_env_int("CHANNEL_ID")
LEADS_CHANNEL_ID = get_env_int("LEADS_CHANNEL_ID")

# Avtovoronka video ID lari
STEP2_VIDEO_ID = get_env_int("STEP2_VIDEO_ID")
CASE1_VIDEO_ID = get_env_int("CASE1_VIDEO_ID")
CASE2_VIDEO_ID = get_env_int("CASE2_VIDEO_ID")
CASE3_VIDEO_ID = get_env_int("CASE3_VIDEO_ID")
DEMO_VIDEO_ID = get_env_int("DEMO_VIDEO_ID")

# Do'jim (nurture) sozlamalari
NURTURE_TIME = os.getenv("NURTURE_TIME", "14:00")
NURTURE_DAY_1 = get_env_int("NURTURE_DAY_1", 1)
NURTURE_DAY_2 = get_env_int("NURTURE_DAY_2", 3)
NURTURE_DAY_3 = get_env_int("NURTURE_DAY_3", 5)

NURTURE_VIDEO_2 = get_env_int("NURTURE_VIDEO_2")