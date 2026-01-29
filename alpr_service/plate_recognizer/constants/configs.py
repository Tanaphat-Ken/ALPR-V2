import os 
import ast
from dotenv import load_dotenv

load_dotenv()

# ==================== NEW PIPELINE WEIGHTS ====================
# Updated weights for new pipeline (PlateDetector → PlateSplitter → Province/OCR)
PLATE_DETECTOR_WEIGHT = "models/weights/plate_detector_best.pt"
PLATE_SPLITTER_WEIGHT = "models/weights/plate_splitter_best.pt"
PROVINCE_CLASSIFIER_WEIGHT = "models/weights/province_classifier_best_new_model.pt"
OCR_WEIGHT = "models/weights/upper_ctc_special_best.pt"

# ==================== OLD WEIGHTS (kept for reference, not used) ====================
# CAR_LOCALIZER_WEIGHT = "models/weights/old/yolov8n.pt"
# PLATE_LOCALIZER_WEIGHT = "models/weights/old/license_plate_detector.pt"
# CRAFT_WEIGHT = "models/weights/old/craft_mlt_25k.pth"
# CRAFT_REFINER_WEIGHT = "models/weights/old/craft_refiner_CTW1500.pth"
# CHARACTOR_READER_WEIGHT = "models/weights/old/charactor_reader.pth"

# CRAFT parameters (not used in new pipeline)
# TEXT_THRESHOLD = 0.8
# LINK_THRESHOLD = 0.4
# LOW_TEXT = 0.7

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg"]

ALLOW_ORIGINS = ast.literal_eval(os.getenv("allow_origins", "[]"))
ALLOW_METHODS = ast.literal_eval(os.getenv("allow_methods", "[]"))
ALLOW_HEADERS = ast.literal_eval(os.getenv("allow_headers", "[]"))