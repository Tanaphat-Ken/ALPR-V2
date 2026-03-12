#!/usr/bin/env python3
"""
4.5.1 Unit Test (1) — AI Inference Logic
Tests the YOLOv11-based PlateDetector and CTCOCRReader pipeline
via ImageProcessor.read() without any network/DB dependencies.

Run from inside the plate_recognizer container or local venv:
    cd alpr_service/plate_recognizer
    pytest testing/test_ai_unit.py -v
"""

import sys
import os
import json
import pytest

# Make sure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.image_processor import ImageProcessor
from PIL import Image
import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _synthetic_white_image(width: int = 640, height: int = 480) -> Image.Image:
    """Return a plain white PIL image (no plate — model should handle gracefully)."""
    arr = np.full((height, width, 3), 255, dtype=np.uint8)
    return Image.fromarray(arr)


def _find_test_image():
    """Search for a real plate image near the testing directory."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "test.jpg"),
        os.path.join(os.path.dirname(__file__), "sample.jpg"),
        os.path.join(os.path.dirname(__file__), "plate.jpg"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def processor():
    """Initialise ImageProcessor once per test module (models are expensive)."""
    return ImageProcessor()


@pytest.fixture(scope="module")
def real_plate_image():
    path = _find_test_image()
    if path:
        return Image.open(path).convert("RGB")
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestImageProcessorInit:
    def test_processor_initialises_without_error(self, processor):
        """ImageProcessor must load all sub-models on startup."""
        assert processor is not None


class TestInferenceOutputStructure:
    """Verify the returned JSON structure matches the contract."""

    REQUIRED_KEYS = {"plate_id", "province", "full_plate", "plate_bbox",
                     "car_bbox", "format_flag", "message"}

    def test_output_has_all_required_keys_on_blank_image(self, processor):
        """Even with no detectable plate, all keys must be present."""
        image = _synthetic_white_image()
        result = processor.read(image)

        assert isinstance(result, dict), "Result must be a dict (JSON-serialisable)"
        missing = self.REQUIRED_KEYS - result.keys()
        assert not missing, f"Missing keys in result: {missing}"

    def test_result_is_json_serialisable(self, processor):
        """Result must be JSON-serialisable (no numpy arrays etc.)."""
        image = _synthetic_white_image()
        result = processor.read(image)
        try:
            json.dumps(result, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            pytest.fail(f"Result is not JSON-serialisable: {exc}")

    def test_plate_bbox_is_list_or_none(self, processor):
        image = _synthetic_white_image()
        result = processor.read(image)
        assert result["plate_bbox"] is None or isinstance(result["plate_bbox"], list), \
            "plate_bbox must be a list [x1,y1,x2,y2] or None"

    def test_car_bbox_is_list_or_none(self, processor):
        image = _synthetic_white_image()
        result = processor.read(image)
        assert result["car_bbox"] is None or isinstance(result["car_bbox"], list), \
            "car_bbox must be a list [x1,y1,x2,y2] or None"


class TestInferenceWithRealPlateImage:
    """Run only when a real plate image is available."""

    def test_real_image_returns_plate_id(self, processor, real_plate_image):
        if real_plate_image is None:
            pytest.skip("No test plate image found — place test.jpg in testing/")

        result = processor.read(real_plate_image)
        assert isinstance(result.get("plate_id"), str), \
            f"Expected string plate_id, got: {result.get('plate_id')}"

    def test_real_image_bbox_is_four_element_list(self, processor, real_plate_image):
        if real_plate_image is None:
            pytest.skip("No test plate image found — place test.jpg in testing/")

        result = processor.read(real_plate_image)
        bbox = result.get("plate_bbox")
        assert isinstance(bbox, list) and len(bbox) == 4, \
            f"plate_bbox must be [x1,y1,x2,y2], got: {bbox}"

    def test_real_image_province_is_string(self, processor, real_plate_image):
        if real_plate_image is None:
            pytest.skip("No test plate image found — place test.jpg in testing/")

        result = processor.read(real_plate_image)
        assert isinstance(result.get("province"), (str, type(None))), \
            f"province must be str or None, got: {type(result.get('province'))}"


class TestReadFromPlateCrop:
    """Test the skip-detector variant that takes a pre-cropped plate image."""

    REQUIRED_KEYS = {"plate_id", "province", "full_plate", "plate_bbox",
                     "format_flag", "message"}

    def test_read_from_plate_crop_returns_required_keys(self, processor):
        crop = _synthetic_white_image(width=200, height=80)
        result = processor.read_from_plate_crop(crop)
        missing = self.REQUIRED_KEYS - result.keys()
        assert not missing, f"Missing keys: {missing}"
