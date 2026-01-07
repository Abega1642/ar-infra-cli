"""Configuration for AR-Infra CLI (especially the env variables)."""

import os

from dotenv import load_dotenv


load_dotenv()


DEFAULT_BOT_ID = "123456789"
DEFAULT_BOT_SLUG = "ar-infra-bot"

BOT_ID = os.getenv("BOT_ID", DEFAULT_BOT_ID)
BOT_SLUG = os.getenv("BOT_SLUG", DEFAULT_BOT_SLUG)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)
