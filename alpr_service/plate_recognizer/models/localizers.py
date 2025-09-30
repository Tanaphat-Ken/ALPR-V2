import os
import torch
from PIL import Image
from ultralytics import YOLO
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from constants import configs
from libs import craft_utils as utils
from models.craft.basenet import CRAFT
from models.craft.refinenet import RefineNet

from libs.logging import logger

class CarLocalizer:
  def __init__(self, weight_path=configs.CAR_LOCALIZER_WEIGHT):
    self.vehicle_class_ids = [2, 3, 5, 7]
    self.model = YOLO(weight_path)

  def predict(self, image):
    result = self.model(image)
    detections = []
    for detection in result[0].boxes:
      class_id = int(detection.cls.item())
      if class_id in self.vehicle_class_ids:
        confidence = float(detection.conf.item())
        bbox = detection.xywh.tolist()
        detections.append({
          "class_id": class_id,
          "class_name": { 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck' }[class_id],
          "confidence": confidence,
          "bbox": bbox
        })
    return detections

class PlateLocalizer:
  def __init__(self, weight_path=configs.PLATE_LOCALIZER_WEIGHT, device="cpu"):
    self.model = YOLO(weight_path).to(device)

  def predict(self, image):
    result = self.model(image)
    detections = []
    for detection in result[0].boxes:
      class_id = int(detection.cls.item())
      confidence = float(detection.conf.item())
      bbox = detection.xywh.tolist()
      detections.append({
        "class_id": class_id,
        "class_name": { 0: 'license plate' }[class_id],
        "confidence": confidence,
        "bbox": bbox
      })
    return detections

class TextRegionDetector:
  def __init__(self):
    self.net = CRAFT()
    self.refine_net = RefineNet()
    self.net_weight = configs.CRAFT_WEIGHT
    self.refinenet_weight = configs.CRAFT_REFINER_WEIGHT

    if torch.cuda.is_available():
      self.net.to('cuda')
      self.net.load_state_dict(utils.copyStateDict(torch.load(self.net_weight, weights_only=True)))
      self.refine_net.load_state_dict(utils.copyStateDict(torch.load(self.refinenet_weight, weights_only=True)))
      self.refine_net = self.refine_net.cuda()
      self.refine_net = torch.nn.DataParallel(self.refine_net)
    else:
      self.net.load_state_dict(utils.copyStateDict(torch.load(self.net_weight, map_location='cpu', weights_only=True)))
      self.refine_net.load_state_dict(utils.copyStateDict(torch.load(self.refinenet_weight, map_location='cpu', weights_only=True)))

    self.refine_net.eval()
  
  def predict(self, image):
    img_resized, target_ratio, size_heatmap = utils.resize_aspect_ratio(image)
    ratio_h = ratio_w = 1 / target_ratio

    x = utils.normalizeMeanVariance(img_resized)
    x = utils.addingBatchDimension(x)

    if torch.cuda.is_available():
      x = x.cuda()
    
    with torch.no_grad():
      y, feature = self.net(x)
    
    score_text = y[0,:,:,0].cpu().data.numpy()
    score_link = y[0,:,:,1].cpu().data.numpy()

    with torch.no_grad():
      output_refiner = self.refine_net(y, feature)
    score_link = output_refiner[0,:,:,0].cpu().data.numpy()

    text_threshold = configs.TEXT_THRESHOLD
    link_threshold = configs.LINK_THRESHOLD
    low_text = configs.LOW_TEXT

    boxes, polys = utils.getDetBoxes(score_text, score_link, text_threshold, link_threshold, low_text, poly=True)

    boxes = utils.adjustResultCoordinates(boxes, ratio_w, ratio_h)
    polys = utils.adjustResultCoordinates(polys, ratio_w, ratio_h)
    for k in range(len(polys)):
      if polys[k] is None: polys[k] = boxes[k]
    
    if len(polys):
      polys = polys if isinstance(polys, list) else polys.tolist()
      for i in range(len(polys)):
        polys[i] = polys[i] if isinstance(polys[i], list) else polys[i].tolist()
    
    return polys
    
class CharacterReader:
  def __init__(self, weight_path: str | None = None, base_model_id: str = "openthaigpt/thai-trocr", device: str | None = None):
    """Initialize character reader (TrOCR).

    Loading priority:
    1) Explicit weight_path argument
    2) configs.CHARACTOR_READER_WEIGHT (can be a folder saved via save_pretrained, or a .pth state_dict)
    3) Fallback to HF model id (base_model_id)
    """

    self.device = torch.device(device) if device in ("cpu", "cuda") else torch.device("cuda" if torch.cuda.is_available() else "cpu")

    source = weight_path or getattr(configs, "CHARACTOR_READER_WEIGHT", None)

    def _load_from_dir(dir_path: str):
      logger.info(f"Loading TrOCR from directory: {dir_path}")
      processor = TrOCRProcessor.from_pretrained(dir_path)
      model = VisionEncoderDecoderModel.from_pretrained(dir_path)
      return processor, model

    def _maybe_extract_state_dict(obj):
      # support common checkpoint formats
      if isinstance(obj, dict):
        for key in ("state_dict", "model_state_dict", "model"):  # try typical wrappers
          if key in obj and isinstance(obj[key], dict):
            return obj[key]
      return obj if isinstance(obj, dict) else obj

    def _strip_prefix(sd: dict, prefix: str = "module."):
      if not isinstance(sd, dict):
        return sd
      return { (k[len(prefix):] if k.startswith(prefix) else k): v for k, v in sd.items() }

    try:
      if isinstance(source, str) and os.path.isdir(source):
        self.processor, self.model = _load_from_dir(source)
      elif isinstance(source, str) and os.path.isfile(source):
        logger.info(f"Loading TrOCR state_dict from file: {source}")
        # load base arch then load state dict
        self.processor = TrOCRProcessor.from_pretrained(base_model_id)
        self.model = VisionEncoderDecoderModel.from_pretrained(base_model_id)
        state = torch.load(source, map_location="cpu")
        state_dict = _maybe_extract_state_dict(state)
        state_dict = _strip_prefix(state_dict, prefix="module.")
        missing, unexpected = self.model.load_state_dict(state_dict, strict=False)
        if missing:
          logger.warning(f"TrOCR load_state_dict missing keys: {len(missing)}")
        if unexpected:
          logger.warning(f"TrOCR load_state_dict unexpected keys: {len(unexpected)}")
      else:
        # fallback to HF model id
        logger.info(f"Loading TrOCR from HF model: {base_model_id}")
        self.processor = TrOCRProcessor.from_pretrained(base_model_id)
        self.model = VisionEncoderDecoderModel.from_pretrained(base_model_id)
    except Exception as e:
      logger.error(f"Failed to load CharacterReader weights from '{source}': {e}. Falling back to base model '{base_model_id}'.")
      self.processor = TrOCRProcessor.from_pretrained(base_model_id)
      self.model = VisionEncoderDecoderModel.from_pretrained(base_model_id)

    self.model.to(self.device)
    self.model.eval()

  def predict(self, image_list):
    if not isinstance(image_list, list):
      raise TypeError("Input must be a list of PIL images.")

    for image in image_list:
      if not isinstance(image, Image.Image):
        raise TypeError(f"All elements in the list must be PIL images. Got: {type(image)}")

    pixel_values = self.processor(images=image_list, return_tensors="pt").pixel_values.to(self.device)
    generated_ids = self.model.generate(pixel_values)
    generated_texts = self.processor.batch_decode(generated_ids, skip_special_tokens=True)

    return generated_texts