import os
from dotenv import load_dotenv

load_dotenv()

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5003))
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

# AI Model Configuration
PLATE_RECOGNIZER_URL = os.getenv("PLATE_RECOGNIZER_URL", "http://localhost:5000/api/v1/image/process")
TRACKER_WEIGHT = os.getenv("TRACKER_WEIGHT", "yolov8n.pt")

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "alpr_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Timezone
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Bangkok")

# Stream Configuration
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg"]
FPS_LIMIT = int(os.getenv("FPS_LIMIT", 10))
FRAME_SKIP = int(os.getenv("FRAME_SKIP", 3))

# CORS Configuration
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "http://localhost:3000").split(",")
ALLOW_METHODS = ["*"]
ALLOW_HEADERS = ["*"]

# Paths
IMAGES_PATH = "images_logs"
CAMERAS_CONFIG_PATH = "configs/cameras.json"

# Database (MVP: ปิดไว้ก่อน)
DATABASE_ENABLED = os.getenv("DATABASE_ENABLED", "false").lower() == "true"
