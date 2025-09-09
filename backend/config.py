from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env from project root (parent of backend folder)
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


def getenv_required(key: str) -> str:
    value = os.getenv(key)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


# Database configuration
DB_USER = getenv_required("DB_USER")
DB_PASSWORD = getenv_required("DB_PASSWORD")
DB_HOST = getenv_required("DB_HOST")
DB_PORT = getenv_required("DB_PORT")
DB_NAME = getenv_required("DB_NAME")

# AWS / S3
AWS_S3_BUCKET = getenv_required("AWS_S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
