import os
import torch
import torch.nn.functional as F
from PIL import Image
import numpy as np
import cv2
from ultralytics import YOLO
import timm
import torchvision.transforms as T
from constants import configs
from libs.logging import logger


# ==================== NEW PIPELINE MODELS ====================

class PlateDetector:
  """YOLO-based plate detector (replaces CarLocalizer + PlateLocalizer)"""
  def __init__(self, weight_path=configs.PLATE_DETECTOR_WEIGHT, device=None):
    self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    self.model = YOLO(weight_path).to(self.device)
    logger.info(f"PlateDetector loaded from {weight_path} on {self.device}")

  def predict(self, image, conf=0.25, iou=0.7, imgsz=1280):
    """
    Predict plate bounding boxes from image (PIL Image or numpy array)
    Returns: list of dicts with bbox, confidence
    """
    results = self.model.predict(image, conf=conf, iou=iou, imgsz=imgsz, verbose=False)
    detections = []
    if results and len(results) > 0:
      result = results[0]
      if result.boxes is not None:
        boxes = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        for box, conf_val in zip(boxes, confs):
          detections.append({
            "bbox": box.tolist(),  # [x1, y1, x2, y2]
            "confidence": float(conf_val)
          })
    return detections


class PlateSplitter:
  """YOLO-based splitter: splits plate into license_text (class 0) and province (class 1)"""
  def __init__(self, weight_path=configs.PLATE_SPLITTER_WEIGHT, device=None):
    self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    self.model = YOLO(weight_path).to(self.device)
    logger.info(f"PlateSplitter loaded from {weight_path} on {self.device}")

  def predict(self, plate_image, conf=0.25, iou=0.6, imgsz=640):
    """
    Predict text/province regions in a plate crop.
    Returns: dict with 'license_text' and 'province' keys, each containing bbox/conf or None
    """
    results = self.model.predict(plate_image, conf=conf, iou=iou, imgsz=imgsz, verbose=False)
    output = {"license_text": None, "province": None}
    
    if results and len(results) > 0:
      result = results[0]
      if result.boxes is not None:
        boxes = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        clss = result.boxes.cls.cpu().numpy().astype(int)
        
        # Find best box for each class
        text_idxs = [i for i, c in enumerate(clss) if c == 0]
        prov_idxs = [i for i, c in enumerate(clss) if c == 1]
        
        if text_idxs:
          best_t = max(text_idxs, key=lambda i: confs[i])
          output["license_text"] = {
            "bbox": boxes[best_t].tolist(),
            "confidence": float(confs[best_t])
          }
        
        if prov_idxs:
          best_p = max(prov_idxs, key=lambda i: confs[i])
          output["province"] = {
            "bbox": boxes[best_p].tolist(),
            "confidence": float(confs[best_p])
          }
    
    return output


class ProvinceClassifier:
  """Province classifier using timm (mobilenetv3 or efficientnet)"""
  def __init__(self, weight_path=configs.PROVINCE_CLASSIFIER_WEIGHT, device=None):
    self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    
    if not os.path.exists(weight_path):
      raise FileNotFoundError(f"Province classifier checkpoint not found: {weight_path}")
    
    ckpt = torch.load(weight_path, map_location=self.device)
    model_name = ckpt.get('model_name', 'mobilenetv3_small_100')
    num_classes = ckpt.get('num_classes', 77)
    
    self.model = timm.create_model(model_name, pretrained=False, num_classes=num_classes, in_chans=3).to(self.device)
    self.model.load_state_dict(ckpt['state_dict'])
    self.model.eval()
    
    # Load idx2label mapping
    idx2label = ckpt.get('idx2label', None)
    if idx2label is None:
      label2idx = ckpt.get('label2idx', {})
      idx2label = {int(v): k for k, v in label2idx.items()}
    else:
      idx2label = {int(k): v for k, v in idx2label.items()}
    self.idx2label = idx2label
    
    self.transform = T.Compose([
      T.Resize((32, 128)),
      T.ToTensor(),
      T.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ])
    
    logger.info(f"ProvinceClassifier loaded from {weight_path} ({model_name}, {num_classes} classes) on {self.device}")

  def predict(self, province_image, topk=1):
    """
    Predict province from image crop (PIL or numpy BGR).
    Returns: list of (label, confidence) tuples, sorted by confidence desc
    """
    if province_image is None:
      return []
    
    # Convert to PIL RGB
    if isinstance(province_image, np.ndarray):
      if len(province_image.shape) == 3 and province_image.shape[2] == 3:
        # Assume BGR
        rgb = cv2.cvtColor(province_image, cv2.COLOR_BGR2RGB)
      else:
        rgb = province_image
      img = Image.fromarray(rgb)
    else:
      img = province_image.convert('RGB')
    
    x = self.transform(img).unsqueeze(0).to(self.device)
    
    with torch.no_grad():
      logits = self.model(x)
      probs = F.softmax(logits, dim=1).squeeze(0)
    
    k = min(topk, probs.numel())
    vals, idxs = torch.topk(probs, k=k)
    
    results = []
    for v, i in zip(vals.cpu().tolist(), idxs.cpu().tolist()):
      label = self.idx2label.get(int(i), str(int(i)))
      results.append((label, float(v)))
    
    return results


class CRNN(torch.nn.Module):
  """CTC-based OCR model (CRNN)"""
  def __init__(self, num_classes: int, img_height: int = 32):
    super().__init__()
    self.cnn = torch.nn.Sequential(
      torch.nn.Conv2d(1, 64, 3, 1, 1), torch.nn.BatchNorm2d(64), torch.nn.ReLU(True),
      torch.nn.MaxPool2d(2, 2),
      torch.nn.Conv2d(64, 128, 3, 1, 1), torch.nn.BatchNorm2d(128), torch.nn.ReLU(True),
      torch.nn.MaxPool2d(2, 2),
      torch.nn.Conv2d(128, 256, 3, 1, 1), torch.nn.BatchNorm2d(256), torch.nn.ReLU(True),
      torch.nn.Conv2d(256, 256, 3, 1, 1), torch.nn.BatchNorm2d(256), torch.nn.ReLU(True),
      torch.nn.MaxPool2d((2, 1), (2, 1)),
      torch.nn.Conv2d(256, 512, 3, 1, 1), torch.nn.BatchNorm2d(512), torch.nn.ReLU(True),
      torch.nn.MaxPool2d((2, 1), (2, 1)),
    )
    self.rnn = torch.nn.LSTM(512 * (img_height // 16), 256, num_layers=2, batch_first=True, bidirectional=True)
    self.classifier = torch.nn.Linear(256 * 2, num_classes)

  def forward(self, x: torch.Tensor) -> torch.Tensor:
    feats = self.cnn(x)
    b, c, h, w = feats.size()
    feats = feats.permute(0, 3, 1, 2).contiguous()
    feats = feats.view(b, w, c * h)
    rnn_out, _ = self.rnn(feats)
    logits = self.classifier(rnn_out)
    return logits.permute(1, 0, 2)  # (T, B, C) for CTC


class CTCOCRReader:
  """CTC OCR model for reading license plate text"""
  def __init__(self, weight_path=configs.OCR_WEIGHT, device=None):
    self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    
    if not os.path.exists(weight_path):
      raise FileNotFoundError(f"OCR checkpoint not found: {weight_path}")
    
    ckpt = torch.load(weight_path, map_location=self.device)
    idx_to_char = ckpt.get('idx_to_char', None)
    if idx_to_char is None:
      raise ValueError('idx_to_char not found in OCR checkpoint')
    
    self.idx_to_char = idx_to_char
    self.model = CRNN(num_classes=len(idx_to_char)).to(self.device)
    self.model.load_state_dict(ckpt['model_state'])
    self.model.eval()
    
    self.transform = T.Compose([
      T.Resize((32, 128)),
      T.ToTensor(),
      T.Normalize((0.5,), (0.5,)),
    ])
    
    logger.info(f"CTCOCRReader loaded from {weight_path} on {self.device}")

  def predict(self, text_image):
    """
    Predict text from image crop (PIL or numpy BGR).
    Returns: string
    """
    if text_image is None:
      return ""
    
    # Convert to grayscale PIL
    if isinstance(text_image, np.ndarray):
      if len(text_image.shape) == 3:
        gray = cv2.cvtColor(text_image, cv2.COLOR_BGR2GRAY)
      else:
        gray = text_image
      img = Image.fromarray(gray)
    else:
      img = text_image.convert('L')
    
    x = self.transform(img).unsqueeze(0).to(self.device)
    
    with torch.no_grad():
      logits = self.model(x)
      text = self._greedy_decode(logits)
    
    return text

  def _greedy_decode(self, logits: torch.Tensor) -> str:
    """CTC greedy decoding"""
    probs = logits.softmax(2)
    indices = probs.argmax(2).permute(1, 0)  # (B, T)
    seq = indices[0].tolist()
    prev = None
    chars = []
    for idx in seq:
      if idx != 0 and idx != prev:
        chars.append(self.idx_to_char[idx])
      prev = idx
    return "".join(chars)