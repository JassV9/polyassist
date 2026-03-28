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

    def extract_text_multi_strategy(self, frame: np.ndarray, region_name: str) -> str | None:
        """
        Try multiple preprocessing strategies and return the result
        with the most digit content (best for HUD numbers).
        """
        if region_name not in self.calibration.regions:
            return None

        x, y, w, h = self.calibration.regions[region_name]
        roi = frame[y:y+h, x:x+w]

        best_text = None
        best_digit_count = -1

        for name, preprocessor in [
            ("white_thresh", self._preprocess_white_threshold),
            ("otsu", self._preprocess_otsu),
            ("adaptive", self._preprocess_adaptive),
        ]:
            try:
                processed = preprocessor(roi)
                config = '--psm 7'
                text = pytesseract.image_to_string(processed, config=config).strip()
                if text:
                    digit_count = sum(c.isdigit() for c in text)
                    logger.debug(f"OCR strategy '{name}': '{text}' ({digit_count} digits)")
                    if digit_count > best_digit_count:
                        best_digit_count = digit_count
                        best_text = text
            except Exception as e:
                logger.debug(f"OCR strategy '{name}' failed: {e}")

        return best_text

    def _preprocess_white_threshold(self, image: np.ndarray) -> np.ndarray:
        """Fixed high threshold -- isolates white text on any background."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        return thresh

    def _preprocess_otsu(self, image: np.ndarray) -> np.ndarray:
        """Otsu auto-threshold -- works well on dark backgrounds."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def _preprocess_adaptive(self, image: np.ndarray) -> np.ndarray:
        """Adaptive threshold -- handles varying local contrast."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, -10
        )
        return thresh

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Default preprocessing -- fixed white threshold."""
        return self._preprocess_white_threshold(image)

    def extract_game_stats(self, frame: np.ndarray) -> dict[str, str]:
        """
        Extract turn, stars, score, and star_income from the HUD.

        The HUD numbers row always shows: SCORE ★STARS TURN/MAX
        Example: "1,440 ★11 7/30" -> score=1440, stars=11, turn=7

        Star income (+N) comes from the label row above.
        """
        stats = {"turn": "0", "stars": "0", "score": "0", "star_income": "0"}

        if "hud_strip" in self.calibration.regions:
            text = self.extract_text_multi_strategy(frame, "hud_strip")
            if text:
                logger.debug(f"HUD strip raw: '{text}'")
                # Merge comma-separated digits (e.g. "1,440" -> "1440")
                cleaned = re.sub(r'(\d),(\d)', r'\1\2', text)
                numbers = re.findall(r'\d+', cleaned)
                logger.debug(f"HUD numbers (cleaned): {numbers}")

                # Pattern is always: [score, stars, turn, turn_max]
                # "7/30" splits into two numbers; turn_max is discarded
                if len(numbers) >= 3:
                    stats["score"] = numbers[0]
                    stats["stars"] = numbers[1]
                    stats["turn"] = numbers[2]
                    # numbers[3] if present is turn_max, ignore it
                elif len(numbers) == 2:
                    stats["score"] = numbers[0]
                    stats["stars"] = numbers[1]
                elif len(numbers) == 1:
                    stats["score"] = numbers[0]

        # Star income comes from the label row: "Score  Stars (+4)  Turn"
        if "hud_labels" in self.calibration.regions:
            label_text = self.extract_text_multi_strategy(frame, "hud_labels")
            if label_text:
                logger.debug(f"HUD labels raw: '{label_text}'")
                income_match = re.search(r'\+\s*(\d+)', label_text)
                if income_match:
                    stats["star_income"] = income_match.group(1)

        return stats
