import os
import numpy as np
import supervision as sv
from ultralytics import YOLO

from src.constants import configs
from src.utils.logging import logger

class VideoPlateTracker:
    """
    Track license plates in video stream using PlateDetector (not car detection).
    Better performance on grayscale/dark images with ALPR-specific trained model.
    """
    def __init__(self, selected_classes=[0]):
        # ใช้โมเดล plate detector
        model_path = os.path.join("src", "models", "weights", "plate_detector_best.pt")
        if not os.path.exists(model_path):
            logger.warning(f"Plate detector model not found at {model_path}, using default yolov8n.pt")
            model_path = configs.TRACKER_WEIGHT
        
        self.model = YOLO(model_path)
        self.selected_classes = selected_classes  # class 0 = license plate
        self.tracker = sv.ByteTrack()

        self.display_item = {
            "idx": None,
            "frame": None,
            "bbox": None,
            "area": 0
        }

    def process_frame(self, frame):
        try:
            results = self.model(frame, imgsz=1280, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)
            detections = detections[np.isin(detections.class_id, self.selected_classes)]

            detections = self.tracker.update_with_detections(detections)

            if len(detections) > 0:
                current_idx = detections.tracker_id[0]
                current_bbox = detections.xyxy[0]
                current_area = self._calculate_area(current_bbox)

                return self._update_display_item(current_idx, current_bbox, current_area, frame)
            else:
                return self._finalize_display_item()

        except Exception as e:
            logger.error(f"Error processing plate detection frame: {e}")
            return None, None

    def _update_display_item(self, current_idx, current_bbox, current_area, frame):
        if self.display_item["idx"] is None or self.display_item["idx"] != current_idx:
            if self.display_item["idx"] is not None:
                # Return cropped plate when plate tracking changes (plate finalized)
                cropped_plate = self._numpy_crop(self.display_item["frame"], self.display_item["bbox"])
                self.display_item.update({
                    "idx": current_idx,
                    "frame": frame,
                    "bbox": current_bbox,
                    "area": current_area,
                })
                return cropped_plate, True  # Return plate crop + detected flag

            self.display_item.update({
                "idx": current_idx,
                "frame": frame,
                "bbox": current_bbox,
                "area": current_area,
            })

        elif current_area > self.display_item["area"]:
            self.display_item.update({
                "frame": frame,
                "bbox": current_bbox,
                "area": current_area,
            })

        return None, None

    def _finalize_display_item(self):
        if self.display_item["idx"] is not None:
            # Return cropped plate when plate leaves (finalized by blank frame or no detection)
            cropped_plate = self._numpy_crop(self.display_item["frame"], self.display_item["bbox"])
            self.display_item = {
                "idx": None,
                "frame": None,
                "bbox": None,
                "area": 0
            }
            return cropped_plate, True  # Return plate crop + detected flag
        return None, None

    def _numpy_crop(self, image, bbox):
        height, width = image.shape[:2]
        x1, y1, x2, y2 = bbox
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(width, int(x2))
        y2 = min(height, int(y2))
        return image[y1:y2, x1:x2]

    def _calculate_area(self, bbox):
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)


class VideoCarTracker:
    """
    ติดตามรถในวิดีโอและเลือกรูปที่ชัดที่สุด (พื้นที่ใหญ่สุด)
    ใช้ YOLO + ByteTrack
    DEPRECATED: Use VideoPlateTracker instead for better ALPR performance
    """
    def __init__(self, model=None, selected_classes=[2, 5, 7]):
        logger.warning("VideoCarTracker is deprecated, use VideoPlateTracker for better ALPR performance")
        if model is None:
            model = YOLO(configs.TRACKER_WEIGHT)
        self.model = model
        self.selected_classes = selected_classes  # 2=car, 5=bus, 7=truck
        self.tracker = sv.ByteTrack()

        self.display_item = {
            "idx": None,
            "frame": None,
            "bbox": None,
            "area": 0
        }

    def process_frame(self, frame):
        """ประมวลผล frame เดียว"""
        try:
            results = self.model(frame, imgsz=1280, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)
            detections = detections[np.isin(detections.class_id, self.selected_classes)]
            
            detections = self.tracker.update_with_detections(detections)
            
            if len(detections) > 0:
                current_idx = detections.tracker_id[0]
                current_bbox = detections.xyxy[0]
                current_area = self._calculate_area(current_bbox)
                
                return self._update_display_item(current_idx, current_bbox, current_area, frame)
            else:
                return self._finalize_display_item()

        except Exception as e:
            logger.error(f"Error processing YOLO frame: {e}")
            return None, None

    def _update_display_item(self, current_idx, current_bbox, current_area, frame):
        """อัพเดท display item ถ้ารถคันใหม่หรือรูปชัดกว่า"""
        if self.display_item["idx"] is None or self.display_item["idx"] != current_idx:
            if self.display_item["idx"] is not None:
                # รถคันเก่าขับออกไปแล้ว → ส่งรูปที่ชัดที่สุด
                cropped_image = self._numpy_crop(self.display_item["frame"], self.display_item["bbox"])
                cropped_bbox = self.display_item["bbox"]
                self.display_item.update({
                    "idx": current_idx,
                    "frame": frame,
                    "bbox": current_bbox,
                    "area": current_area,
                })
                return cropped_image, cropped_bbox

            # รถคันใหม่
            self.display_item.update({
                "idx": current_idx,
                "frame": frame,
                "bbox": current_bbox,
                "area": current_area,
            })

        elif current_area > self.display_item["area"]:
            # รถคันเดิม แต่ชัดกว่า (ใกล้กล้องมากขึ้น)
            self.display_item.update({
                "frame": frame,
                "bbox": current_bbox,
                "area": current_area,
            })

        return None, None

    def _finalize_display_item(self):
        """รถขับออกจากกรอบ → ส่งรูปสุดท้าย"""
        if self.display_item["idx"] is not None:
            cropped_image = self._numpy_crop(self.display_item["frame"], self.display_item["bbox"])
            cropped_bbox = self.display_item["bbox"]
            self.display_item = {
                "idx": None,
                "frame": None,
                "bbox": None,
                "area": 0
            }
            return cropped_image, cropped_bbox
        return None, None

    def _numpy_crop(self, image, bbox):
        """Crop รูปรถออกมา"""
        height, width = image.shape[:2]
        x1, y1, x2, y2 = bbox
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(width, int(x2))
        y2 = min(height, int(y2))
        return image[y1:y2, x1:x2]

    def _calculate_area(self, bbox):
        """คำนวณพื้นที่"""
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)