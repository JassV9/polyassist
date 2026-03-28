import mss
import numpy as np
import cv2

from .base import CaptureBackend
from .window_finder import find_polytopia_window
import logging

logger = logging.getLogger(__name__)

class MSSBackend(CaptureBackend):
    def __init__(self, window_title: str = "The Battle of Polytopia"):
        self.window_title = window_title
        self.sct = mss.mss()

    def grab(self, region: tuple[int, int, int, int | None] = None) -> np.ndarray:
        if region:
            x, y, w, h = region
            mss_region = {"top": y, "left": x, "width": w, "height": h}
        else:
            window_rect = self.find_game_window()
            if window_rect:
                x, y, w, h = window_rect
                mss_region = {"top": y, "left": x, "width": w, "height": h}
            else:
                # Default monitor
                mss_region = self.sct.monitors[1]

        screenshot = self.sct.grab(mss_region)
        # mss returns BGRA, we want BGR for OpenCV
        frame = np.array(screenshot)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    def find_game_window(self) -> tuple[int, int, int, int | None]:
        return find_polytopia_window(self.window_title)
