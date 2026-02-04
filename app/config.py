"""Configuration management for QuarkFlow."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Telegram configuration
TG_API_ID = int(os.getenv("TG_API_ID", "0"))
TG_API_HASH = os.getenv("TG_API_HASH", "")
TG_CHANNEL = os.getenv("TG_CHANNEL", "@D_wusun")
TG_SESSION_NAME = os.getenv("TG_SESSION", "quarkflow")

# Quark configuration
QUARK_COOKIE = os.getenv("QUARK_COOKIE", "")

# Database
DB_PATH = DATA_DIR / "quarkflow.db"

# Worker settings
WORKER_POLL_INTERVAL = int(os.getenv("WORKER_POLL_INTERVAL", "10"))  # seconds
WORKER_CONCURRENT_TASKS = int(os.getenv("WORKER_CONCURRENT_TASKS", "1"))

# Optional: Target folder name for organizing saved files
TARGET_FOLDER_NAME = os.getenv("TARGET_FOLDER_NAME", "")
