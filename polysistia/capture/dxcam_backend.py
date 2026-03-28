import dxcam
import numpy as np

from .base import CaptureBackend
from .window_finder import find_polytopia_window
import logging

logger = logging.getLogger(__name__)

class DXCamBackend(CaptureBackend):
    def __init__(self, window_title: str = "The Battle of Polytopia"):
        self.window_title = window_title
        self.camera = None
        self._initialize_camera()

    def _initialize_camera(self):
        try:
            self.camera = dxcam.create()
            logger.info("DXCam initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize DXCam: {e}")
            self.camera = None

    def grab(self, region: tuple[int, int, int, int | None] = None) -> np.ndarray:
        if not self.camera:
            self._initialize_camera()
            if not self.camera:
                return np.zeros((1, 1, 3), dtype=np.uint8)

        # Region should be (left, top, right, bottom) for dxcam
        if region:
            x, y, w, h = region
            dxcam_region = (x, y, x + w, y + h)
        else:
            window_rect = self.find_game_window()
            if window_rect:
                x, y, w, h = window_rect
                dxcam_region = (x, y, x + w, y + h)
            else:
                dxcam_region = None

        frame = self.camera.grab(region=dxcam_region)
        if frame is None:
            return np.zeros((1, 1, 3), dtype=np.uint8)

        # dxcam returns RGB, we want BGR for OpenCV
        import cv2
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    def find_game_window(self) -> tuple[int, int, int, int | None]:
        return find_polytopia_window(self.window_title)
