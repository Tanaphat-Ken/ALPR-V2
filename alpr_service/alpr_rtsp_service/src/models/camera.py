from dataclasses import dataclass
from typing import Optional

@dataclass
class Camera:
    id: str
    name: str
    rtsp_url: str
    location: str
    enabled: bool = False
    fps: int = 10
    frame_skip: int = 3
    
    def __str__(self):
        return f"Camera({self.id}, {self.name}, enabled={self.enabled})"
