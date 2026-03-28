import pytesseract
import cv2
import numpy as np
import re
import logging

from ..config import Calibration

logger = logging.getLogger(__name__)


class OCR:
    def __init__(self, calibration: Calibration):
        self.calibration = calibration
        pytesseract.pytesseract.tesseract_cmd = calibration.tesseract_cmd

    def extract_text(self, frame: np.ndarray, region_name: str) -> str | None:
        """Extract text from a specific calibration region."""
        if region_name not in self.calibration.regions:
            return None

        x, y, w, h = self.calibration.regions[region_name]
        roi = frame[y:y+h, x:x+w]
        processed_roi = self._preprocess(roi)

        config = '--psm 7'
        text = pytesseract.image_to_string(processed_roi, config=config).strip()
        return text if text else None

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def extract_game_stats(self, frame: np.ndarray) -> dict[str, str]:
        """
        Extract turn, stars, score from the HUD strip.
        Reads the entire top HUD as one line and parses: "985 *6 4/30"
        -> score=985, stars=6, turn=4
        """
        stats = {"turn": "0", "stars": "0", "score": "0"}

        # Try single-strip HUD approach first
        if "hud_strip" in self.calibration.regions:
            text = self.extract_text(frame, "hud_strip")
            if text:
                logger.debug(f"HUD strip raw: '{text}'")
                numbers = re.findall(r'\d+', text)
                logger.debug(f"HUD numbers: {numbers}")
                if len(numbers) >= 3:
                    stats["score"] = numbers[0]
                    stats["stars"] = numbers[1]
                    stats["turn"] = numbers[2]
                elif len(numbers) == 2:
                    stats["score"] = numbers[0]
                    stats["turn"] = numbers[1]
                elif len(numbers) == 1:
                    stats["score"] = numbers[0]
            return stats

        # Fallback: individual region approach
        for region in ["turn", "stars", "score"]:
            text = self.extract_text(frame, region)
            if text:
                digits = "".join(filter(str.isdigit, text))
                stats[region] = digits if digits else "0"
            else:
                stats[region] = "0"

        return stats
