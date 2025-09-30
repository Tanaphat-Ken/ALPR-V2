from constants import format_flag, reponse_message
from models.localizers import CarLocalizer, PlateLocalizer, TextRegionDetector, CharacterReader
from libs import utils
from libs.logging import logger
import numpy as np

class ImageProcessor:
  def __init__(self, use_craft: bool = False):
    self.car_localizer = CarLocalizer()
    self.plate_localizer = PlateLocalizer()
    self.text_region_detector = TextRegionDetector()
    self.characters_reader = CharacterReader()
    self.use_craft = use_craft
  
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

    if car_bbox is None:
      car_detection_list = self.car_localizer.predict(image)

      car_image = None
      if len(car_detection_list) == 0: 
        car_image = image
      else:
        car_bbox = utils.find_largest_bbox(car_detection_list)
        car_image = image.crop(tuple(car_bbox))

    else:
      car_image = image

    plate_detection_list = self.plate_localizer.predict(car_image)

    plate_image = None
    plate_bbox = None
    if len(plate_detection_list) == 0: 
      plate_image = car_image
    else:
      plate_bbox = utils.find_largest_bbox(plate_detection_list)
      plate_image = car_image.crop(tuple(plate_bbox))

    # If requested, detect text regions with CRAFT inside plate_image
    outputs = []
    if self.use_craft:
      try:
        # CRAFT expects a numpy image (H, W, C)
        np_img = np.array(plate_image)
        polys = self.text_region_detector.predict(np_img) or []
        # Sort by top-most Y to read top-to-bottom
        def top_y(poly):
          return min(p[1] for p in poly) if poly else 0
        polys = [p for p in polys if p is not None]
        polys.sort(key=top_y)

        # Crop each polygon region (rectangular crop around polygon) and OCR
        crops = []
        for poly in polys:
          try:
            crop = utils.crop_4point_image(plate_image, poly)
            crops.append(crop)
          except Exception as e:
            logger.warning(f"CRAFT crop failed: {e}")
        if crops:
          outputs = self.characters_reader.predict(crops)
        else:
          # Fallback to direct OCR on the plate crop
          outputs = self.characters_reader.predict([plate_image])
      except Exception as e:
        logger.warning(f"CRAFT predict failed: {e}; falling back to direct OCR")
        outputs = self.characters_reader.predict([plate_image])
    else:
      outputs = self.characters_reader.predict([plate_image])

    return self._result_format(
      car_bbox=utils.convert_2_to_4_point(car_bbox),
      plate_bbox=utils.convert_2_to_4_point(plate_bbox),
      text_bbox_list=None,
      plate_id=outputs[0] if len(outputs) > 0 else None,
      province=outputs[1] if len(outputs) > 1 else None,
      full_plate=" ".join(outputs) if outputs else None,
      format_flag=format_flag.COMPLETE if len(outputs) == 2 else format_flag.WARNING,
      message=reponse_message.PROCESS_SUCCESS
    )