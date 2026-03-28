import dxcam
import numpy as np
import cv2

from .base import CaptureBackend
from .window_finder import find_polytopia_window
import logging

logger = logging.getLogger(__name__)

class DXCamBackend(CaptureBackend):
    def __init__(self, window_title: str = "The Battle of Polytopia"):
        self.window_title = window_title
        self.camera = None
        self.screen_width = 0
        self.screen_height = 0
        self._initialize_camera()

    def _initialize_camera(self):
        try:
            self.camera = dxcam.create()
            # Get screen dimensions from the output metadata
            self.screen_width = self.camera.width
            self.screen_height = self.camera.height
            logger.info(f"DXCam initialized: {self.screen_width}x{self.screen_height}")
        except Exception as e:
            logger.error(f"Failed to initialize DXCam: {e}")
            self.camera = None

    def _clamp_region(self, left, top, right, bottom):
        """Clamp a region to valid screen bounds for DXCam."""
        left = max(0, left)
        top = max(0, top)
        right = min(self.screen_width, right)
        bottom = min(self.screen_height, bottom)
        if right <= left or bottom <= top:
            return None
        return (left, top, right, bottom)

    def grab(self, region: tuple[int, int, int, int] | None = None) -> np.ndarray:
        if not self.camera:
            self._initialize_camera()
            if not self.camera:
                return np.zeros((1, 1, 3), dtype=np.uint8)

        dxcam_region = None

        if region:
            x, y, w, h = region
            dxcam_region = self._clamp_region(x, y, x + w, y + h)
        else:
            window_rect = self.find_game_window()
            if window_rect:
                x, y, w, h = window_rect
                dxcam_region = self._clamp_region(x, y, x + w, y + h)

        frame = self.camera.grab(region=dxcam_region)
        if frame is None:
            return np.zeros((1, 1, 3), dtype=np.uint8)

        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    def find_game_window(self) -> tuple[int, int, int, int] | None:
        return find_polytopia_window(self.window_title)
