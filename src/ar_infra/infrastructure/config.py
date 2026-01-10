import os


BOT_ID = os.getenv("BOT_ID", "__BOT_ID_PLACEHOLDER__")
BOT_SLUG = os.getenv("BOT_SLUG", "__BOT_SLUG_PLACEHOLDER__")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)

if BOT_ID == "__BOT_ID_PLACEHOLDER__":
    BOT_ID = "123456789"

if BOT_SLUG == "__BOT_SLUG_PLACEHOLDER__":
    BOT_SLUG = "ar-infra-bot"
