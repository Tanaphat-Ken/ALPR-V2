import os
import numpy as np
import supervision as sv
from ultralytics import YOLO

from src.constants import configs
from src.utils.logging import logger

# --- Quality filters ---
MIN_CONF = 0.4          # ตัดการตรวจจับที่ confidence ต่ำออกก่อน tracker
MIN_PLATE_AREA = 2300   # ป้ายที่เล็กเกินไป (รถอยู่ไกล) ไม่ส่งไป OCR
# force-finalize: เดิมใช้ 60 (calibrated for frames) → แก้เป็น 8 (calibrated for DETECTION RUNS)
# imgsz=640 + CPU ≈ 0.5-1s/run, frame_skip=1 → ~1-2 runs/sec → 8 runs ≈ 4-8 วินาทีของการดูป้ายแผ่นเดียว
MAX_TRACKED_FRAMES = 8

class VideoPlateTracker:
    """
    Track license plates in video stream using PlateDetector (not car detection).
    Better performance on grayscale/dark images with ALPR-specific trained model.
    """
    def __init__(self, selected_classes=[0], imgsz=1280):
        # ใช้โมเดล plate detector
        model_path = os.path.join("src", "models", "weights", "plate_detector_best.pt")
        if not os.path.exists(model_path):
            logger.warning(f"Plate detector model not found at {model_path}, using default yolov8n.pt")
            model_path = configs.TRACKER_WEIGHT
        
        self.model = YOLO(model_path)
        self.selected_classes = selected_classes  # class 0 = license plate
        self.imgsz = imgsz  # 1280 for video file (accuracy), 640 for RTSP (speed)

        self.display_item = {
            "idx": None,
            "frame": None,
            "bbox": None,
            "area": 0
        }

    def process_frame(self, frame):
        try:
            results = self.model(frame, imgsz=self.imgsz, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)
            detections = detections[np.isin(detections.class_id, self.selected_classes)]

            # --- confidence filter ---
            if detections.confidence is not None:
                detections = detections[detections.confidence >= MIN_CONF]

            # --- ไม่ใช้ ByteTrack: เรามีแค่ป้าย 1 อันในภาพ ใช้ detection โดยตรง ---
            # เลือก detection ที่ confidence สูงสุด
            if len(detections) > 0:
                best_idx = int(np.argmax(detections.confidence))
                current_bbox = detections.xyxy[best_idx]
                current_conf = float(detections.confidence[best_idx])
                current_area = self._calculate_area(current_bbox)

                logger.debug(f"[Tracker] Plate detected: conf={current_conf:.2f} area={current_area:.0f}")

                # area filter: ป้ายเล็กเกินไป (รถอยู่ไกล)
                if current_area < MIN_PLATE_AREA:
                    logger.debug(f"[Tracker] Skipping: area={current_area:.0f} < {MIN_PLATE_AREA}")
                    return None, None

                # ✅ เพิ่ม area: เก็บ frame ที่ชัดที่สุด (area ใหญ่สุด) ไว้ใน display_item
                if self.display_item["area"] == 0 or current_area > self.display_item["area"]:
                    self.display_item.update({"frame": frame, "bbox": current_bbox, "area": current_area})

                # ✅ return crop จาก best frame ที่เก็บไว้
                cropped_plate = self._numpy_crop(self.display_item["frame"], self.display_item["bbox"])
                return cropped_plate, True
            else:
                # plate หายจากภาพ → reset best-frame buffer
                self.display_item = {"idx": None, "frame": None, "bbox": None, "area": 0, "frames_tracked": 0}
                return None, None

        except Exception as e:
            logger.error(f"Error processing plate detection frame: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None

    def _update_display_item(self, current_idx, current_bbox, current_area, frame):
        if self.display_item["idx"] is None or self.display_item["idx"] != current_idx:
            # --- tracker_id เปลี่ยน → finalize ป้ายเก่า ---
            if self.display_item["idx"] is not None:
                # --- area filter: ข้ามป้ายที่เล็กเกินไป (รถอยู่ไกล/ภาพเบลอ) ---
                if self.display_item["area"] < MIN_PLATE_AREA:
                    logger.info(f"Skipping switched plate (area={self.display_item['area']:.0f} < {MIN_PLATE_AREA}) – too small/blurry")
                    self.display_item.update({
                        "idx": current_idx, "frame": frame,
                        "bbox": current_bbox, "area": current_area, "frames_tracked": 0
                    })
                    return None, None

                # Return cropped plate when plate tracking changes (plate finalized)
                cropped_plate = self._numpy_crop(self.display_item["frame"], self.display_item["bbox"])
                self.display_item.update({
                    "idx": current_idx, "frame": frame,
                    "bbox": current_bbox, "area": current_area, "frames_tracked": 0
                })
                return cropped_plate, True  # Return plate crop + detected flag

            # --- ครั้งแรก ---
            self.display_item.update({
                "idx": current_idx, "frame": frame,
                "bbox": current_bbox, "area": current_area, "frames_tracked": 0
            })

        else:
            # --- tracker_id เดิม: update frame ถ้าชัดขึ้น ---
            self.display_item["frames_tracked"] += 1
            if current_area > self.display_item["area"]:
                self.display_item.update({"frame": frame, "bbox": current_bbox, "area": current_area})

            # --- FORCE FINALIZE: plate เดิมนานเกินไป (looping video / รถจอดนิ่ง) ---
            if self.display_item["frames_tracked"] >= MAX_TRACKED_FRAMES:
                if self.display_item["area"] >= MIN_PLATE_AREA:
                    logger.info(f"[Force-finalize] plate tracked {self.display_item['frames_tracked']} frames, sending to OCR")
                    cropped_plate = self._numpy_crop(self.display_item["frame"], self.display_item["bbox"])
                    self.display_item.update({
                        "idx": current_idx, "frame": frame,
                        "bbox": current_bbox, "area": current_area, "frames_tracked": 0
                    })
                    return cropped_plate, True
                else:
                    # ป้ายเล็กเกินไป — reset counter เพื่อรอต่อไป
                    self.display_item["frames_tracked"] = 0

        return None, None

    def _finalize_display_item(self):
        if self.display_item["idx"] is not None:
            # --- area filter: ข้ามป้ายที่เล็กเกินไป ---
            if self.display_item["area"] < MIN_PLATE_AREA:
                logger.info(f"Skipping finalized plate (area={self.display_item['area']:.0f} < {MIN_PLATE_AREA}) – too small/blurry")
                self.display_item = {"idx": None, "frame": None, "bbox": None, "area": 0, "frames_tracked": 0}
                return None, None
            # Return cropped plate when plate leaves (finalized by blank frame or no detection)
            cropped_plate = self._numpy_crop(self.display_item["frame"], self.display_item["bbox"])
            self.display_item = {"idx": None, "frame": None, "bbox": None, "area": 0, "frames_tracked": 0}
            return cropped_plate, True  # Return plate crop + detected flag
        return None, None

    def take_pending_plate(self):
        """ดึง plate ที่กำลัง track อยู่ออกมาโดยไม่ลบทิ้ง (เรียกก่อน reset เพื่อไม่สูญเสีย plate)"""
        return self._finalize_display_item()

    def reset(self):
        """Reset tracker state (เรียกเมื่อ video loop หรือ reconnect)"""
        self.display_item = {"idx": None, "frame": None, "bbox": None, "area": 0, "frames_tracked": 0}

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