import io
from PIL import Image

def is_image(data: bytes) -> bool:
    """Validate if bytes data is a valid image"""
    try:
        image = Image.open(io.BytesIO(data))
        image.verify()
        return True
    except Exception:
        return False
