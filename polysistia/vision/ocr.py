import pytesseract
import cv2
import numpy as np

from ..config import Calibration

class OCR:
    def __init__(self, calibration: Calibration):
        self.calibration = calibration
        pytesseract.pytesseract.tesseract_cmd = calibration.tesseract_cmd

    def extract_text(self, frame: np.ndarray, region_name: str) -> str | None:
        """
        Extract text from a specific region defined in the calibration.
        """
        if region_name not in self.calibration.regions:
            return None

        x, y, w, h = self.calibration.regions[region_name]
        roi = frame[y:y+h, x:x+w]

        # Pre-process image for better OCR
        processed_roi = self._preprocess(roi)

        # OCR
        config = '--psm 7' # Treat the image as a single text line
        text = pytesseract.image_to_string(processed_roi, config=config).strip()

        return text if text else None

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        # Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Upscale
        gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

        # Threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return thresh

    def extract_game_stats(self, frame: np.ndarray) -> dict[str]:
        """
        Extract turn, stars, score from the frame.
        """
        stats = {}
        for region in ["turn", "stars", "score"]:
            text = self.extract_text(frame, region)
            if text:
                # Basic cleaning
                stats[region] = "".join(filter(str.isdigit, text))
            else:
                stats[region] = "0"

        return stats
