import os
import ast
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
PORT = int(os.getenv("PORT", "5000"))
HOST = os.getenv("HOST", "0.0.0.0")
ALLOW_ORIGINS = ast.literal_eval(os.getenv("ALLOW_ORIGINS", "[*]"))
ALLOW_METHODS = ast.literal_eval(os.getenv("ALLOW_METHODS", "[*]"))
ALLOW_HEADERS = ast.literal_eval(os.getenv("ALLOW_HEADERS", "[*]"))
MAX_FILE_SIZE = 50 * 1024 * 1024
WS_MAX_SIZE = 5 * 1024 * 1024  # WebSocket max message size: 5MB (to support full frame images)
TRACKER_WEIGHT = "./src/models/weights/yolov8n.pt" # Deprecated: for VideoCarTracker (car detection)
PLATE_DETECTOR_WEIGHT = "./src/models/weights/plate_detector_best.pt" # For VideoPlateTracker (plate detection)
PLATE_RECOG_BASE_URL = os.getenv("PLATE_RECOG_BASE_URL", "http://localhost:5000/api/v1")

DB_NAME = os.getenv("DB_NAME", "alpr_service")
DB_USER = os.getenv("DB_USER", "alpr")
DB_PASSWORD = os.getenv("DB_PASS", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", 5432)

IMAGES_PATH = "./images_logs"