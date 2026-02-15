from constants import format_flag, reponse_message
from models.localizers import PlateDetector, PlateSplitter, ProvinceClassifier, CTCOCRReader
from libs import utils
from libs.logging import logger
import numpy as np
from PIL import Image
import cv2


class ImageProcessor:
  def __init__(self, device=None):
    """Initialize new pipeline: PlateDetector → PlateSplitter → ProvinceClassifier + OCR"""
    self.plate_detector = PlateDetector(device=device)
    self.plate_splitter = PlateSplitter(device=device)
    self.province_classifier = ProvinceClassifier(device=device)
    self.ocr_reader = CTCOCRReader(device=device)
    logger.info("ImageProcessor initialized with new pipeline (PlateDetector → PlateSplitter → Province/OCR)")
  
  def _result_format(
    self, 
    car_bbox=None, 
    plate_bbox=None, 
    text_bbox_list=None, 
    plate_id=None, 
    province=None,
    full_plate=None,
    format_flag=format_flag.WARNING,
    message=""
  ):
    return { 
      "car_bbox": car_bbox,
      "plate_bbox": plate_bbox,
      "text_bbox_list": text_bbox_list,
      "plate_id": plate_id,
      "province": province,
      "full_plate": full_plate,
      "format_flag": format_flag,
      "message": message
    }

  def read(self, image, car_bbox=None):
    """
    Process image through new pipeline.
    
    Args:
      image: PIL Image or numpy array (BGR)
      car_bbox: Optional car bbox (if provided, crop to car first) - for backward compatibility
    
    Returns:
      dict with plate_bbox, plate_id, province, full_plate, etc.
    """
    
    # Convert to numpy if PIL
    if isinstance(image, Image.Image):
      frame = np.array(image)
      # PIL is RGB, convert to BGR for consistency
      if len(frame.shape) == 3 and frame.shape[2] == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    else:
      frame = image
    
    # If car_bbox provided, crop to that region (backward compatibility)
    if car_bbox is not None:
      try:
        x1, y1, x2, y2 = map(int, car_bbox[:4])
        frame = frame[y1:y2, x1:x2]
      except Exception as e:
        logger.warning(f"Failed to crop car bbox: {e}")
    
    # Step 1: Detect plate
    plate_detections = self.plate_detector.predict(frame, conf=0.25, iou=0.7, imgsz=1280)
    
    if len(plate_detections) == 0:
      logger.warning("No plate detected")
      return self._result_format(
        car_bbox=utils.convert_2_to_4_point(car_bbox) if car_bbox else None,
        format_flag=format_flag.WARNING,
        message="No plate detected"
      )
    
    # Get best plate (highest confidence)
    best_plate = max(plate_detections, key=lambda x: x['confidence'])
    plate_bbox = best_plate['bbox']  # [x1, y1, x2, y2]
    
    # Crop plate region
    x1, y1, x2, y2 = map(int, plate_bbox)
    plate_crop = frame[y1:y2, x1:x2]
    
    if plate_crop.size == 0:
      logger.warning("Empty plate crop")
      return self._result_format(
        car_bbox=utils.convert_2_to_4_point(car_bbox) if car_bbox else None,
        plate_bbox=utils.convert_2_to_4_point(plate_bbox),
        format_flag=format_flag.WARNING,
        message="Empty plate crop"
      )
    
    # Step 2: Split plate into text/province regions
    split_result = self.plate_splitter.predict(plate_crop, conf=0.25, iou=0.6, imgsz=640)
    
    text_region = split_result.get('license_text')
    prov_region = split_result.get('province')
    
    plate_id = None
    province = None
    
    # Step 3a: OCR on license_text region
    if text_region is not None:
      try:
        tx1, ty1, tx2, ty2 = map(int, text_region['bbox'])
        text_crop = plate_crop[ty1:ty2, tx1:tx2]
        plate_id = self.ocr_reader.predict(text_crop)
      except Exception as e:
        logger.warning(f"OCR failed: {e}")
    else:
      logger.warning("No license_text region detected by splitter")
    
    # Step 3b: Province classification
    if prov_region is not None:
      try:
        px1, py1, px2, py2 = map(int, prov_region['bbox'])
        prov_crop = plate_crop[py1:py2, px1:px2]
        prov_results = self.province_classifier.predict(prov_crop, topk=1)
        if prov_results:
          province = prov_results[0][0]  # top-1 province label
      except Exception as e:
        logger.warning(f"Province classification failed: {e}")
    else:
      logger.warning("No province region detected by splitter")
    
    # Build full_plate
    parts = []
    if plate_id:
      parts.append(plate_id)
    if province:
      parts.append(province)
    full_plate = " ".join(parts) if parts else None
    
    # Success flag
    flag = format_flag.COMPLETE if (plate_id or province) else format_flag.WARNING
    msg = "OK" if (plate_id or province) else "Plate detected but OCR/Province failed"
    
    return self._result_format(
      car_bbox=utils.convert_2_to_4_point(car_bbox) if car_bbox else None,
      plate_bbox=utils.convert_2_to_4_point(plate_bbox),
      text_bbox_list=None,  # not used in new pipeline
      plate_id=plate_id,
      province=province,
      full_plate=full_plate,
      format_flag=flag,
      message=msg
    )
  
  def read_from_plate_crop(self, plate_crop_image):
    """
    Process plate crop directly, skipping PlateDetector step.
    Use this when you already have a cropped plate image from external detector.
    
    Args:
      plate_crop_image: PIL Image or numpy array (BGR) of cropped plate
    
    Returns:
      dict with plate_id, province, full_plate, etc.
    """
    
    # Convert to numpy if PIL
    if isinstance(plate_crop_image, Image.Image):
      plate_crop = np.array(plate_crop_image)
      # PIL is RGB, convert to BGR for consistency
      if len(plate_crop.shape) == 3 and plate_crop.shape[2] == 3:
        plate_crop = cv2.cvtColor(plate_crop, cv2.COLOR_RGB2BGR)
    else:
      plate_crop = plate_crop_image
    
    if plate_crop.size == 0:
      logger.warning("Empty plate crop")
      return self._result_format(
        format_flag=format_flag.WARNING,
        message="Empty plate crop"
      )
    
    # Step 1: Split plate into text/province regions (skip PlateDetector)
    split_result = self.plate_splitter.predict(plate_crop, conf=0.25, iou=0.6, imgsz=640)
    
    text_region = split_result.get('license_text')
    prov_region = split_result.get('province')
    
    plate_id = None
    province = None
    
    # Step 2a: OCR on license_text region
    if text_region is not None:
      try:
        tx1, ty1, tx2, ty2 = map(int, text_region['bbox'])
        text_crop = plate_crop[ty1:ty2, tx1:tx2]
        plate_id = self.ocr_reader.predict(text_crop)
      except Exception as e:
        logger.warning(f"OCR failed: {e}")
    else:
      logger.warning("No license_text region detected by splitter")
    
    # Step 2b: Province classification
    if prov_region is not None:
      try:
        px1, py1, px2, py2 = map(int, prov_region['bbox'])
        prov_crop = plate_crop[py1:py2, px1:px2]
        prov_results = self.province_classifier.predict(prov_crop, topk=1)
        if prov_results:
          province = prov_results[0][0]  # top-1 province label
      except Exception as e:
        logger.warning(f"Province classification failed: {e}")
    else:
      logger.warning("No province region detected by splitter")
    
    # Build full_plate
    parts = []
    if plate_id:
      parts.append(plate_id)
    if province:
      parts.append(province)
    full_plate = " ".join(parts) if parts else None
    
    # Success flag
    flag = format_flag.COMPLETE if (plate_id or province) else format_flag.WARNING
    msg = "OK" if (plate_id or province) else "OCR/Province recognition failed"
    
    return self._result_format(
      car_bbox=None,
      plate_bbox=None,  # We don't have plate bbox since we skipped detection
      text_bbox_list=None,
      plate_id=plate_id,
      province=province,
      full_plate=full_plate,
      format_flag=flag,
      message=msg
    )