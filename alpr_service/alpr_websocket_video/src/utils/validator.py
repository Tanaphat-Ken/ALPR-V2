import io

from PIL import Image

def is_image(image_bytes: bytes) -> bool:
  try:
    image = Image.open(io.BytesIO(image_bytes))
    image.verify()
    return True
  except Exception:
    return False