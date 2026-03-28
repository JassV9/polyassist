import numpy as np
import cv2

class ChangeDetector:
    def __init__(self, threshold: float = 0.05):
        self.threshold = threshold
        self.last_frame = None

    def has_changed(self, frame: np.ndarray) -> bool:
        if self.last_frame is None:
            self.last_frame = frame.copy()
            return True

        if frame.shape != self.last_frame.shape:
            self.last_frame = frame.copy()
            return True

        # Mean Absolute Difference
        diff = cv2.absdiff(frame, self.last_frame)
        mean_diff = np.mean(diff) / 255.0

        if mean_diff > self.threshold:
            self.last_frame = frame.copy()
            return True

        return False
