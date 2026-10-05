import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:98989898@localhost:5432/blog_portal")
JWT_SECRET = os.getenv("JWT_SECRET", "8dbc02a04f075ef24b3956f33df9285f31ef1c680ac612bdba39dda06c03498d")
APP_NAME = "DraftFlow Social API"
