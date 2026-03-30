import pytesseract
import cv2
import numpy as np
import re
import logging

from ..config import Calibration

logger = logging.getLogger(__name__)

KNOWN_TRIBES = [
    "xin-xi", "imperius", "bardur", "oumaji", "kickoo",
    "hoodrick", "luxidoor", "vengir", "zebasi", "ai-mo",
    "quetzali", "yadakk", "aquarion", "elyrion", "polaris", "cymanti",
]


class OCR:
    def __init__(self, calibration: Calibration):
        self.calibration = calibration
        pytesseract.pytesseract.tesseract_cmd = calibration.tesseract_cmd

    def extract_text(self, frame: np.ndarray, region_name: str) -> str | None:
        if region_name not in self.calibration.regions:
            return None
        x, y, w, h = self.calibration.regions[region_name]
        roi = frame[y:y+h, x:x+w]
        processed_roi = self._preprocess(roi)
        text = pytesseract.image_to_string(processed_roi, config='--oem 3 --psm 7').strip()
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
                text = pytesseract.image_to_string(
                    processed, config='--oem 3 --psm 7'
                ).strip()
                if text:
                    digit_count = sum(c.isdigit() for c in text)
                    logger.debug(f"OCR strategy '{name}': '{text}' ({digit_count} digits)")
                    if digit_count > best_digit_count:
                        best_digit_count = digit_count
                        best_text = text
            except Exception as e:
                logger.debug(f"OCR strategy '{name}' failed: {e}")

        return best_text

    def extract_text_alpha(self, frame: np.ndarray, region_name: str) -> str | None:
        """Extract alphabetic text (for tribe names, city names)."""
        if region_name not in self.calibration.regions:
            return None
        x, y, w, h = self.calibration.regions[region_name]
        roi = frame[y:y+h, x:x+w]

        best_text = None
        best_len = 0

        for thresh_val in [160, 180, 200]:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            scaled = cv2.resize(gray, None, fx=4.0, fy=4.0, interpolation=cv2.INTER_CUBIC)
            _, thresh = cv2.threshold(scaled, thresh_val, 255, cv2.THRESH_BINARY)
            try:
                text = pytesseract.image_to_string(
                    thresh, config='--oem 3 --psm 7'
                ).strip()
                if text and len(text) > best_len:
                    best_len = len(text)
                    best_text = text
            except Exception:
                pass

        return best_text

    def ocr_roi(self, roi: np.ndarray, mode: str = "alpha") -> str | None:
        """OCR an arbitrary image ROI (not tied to a calibration region)."""
        if roi.size == 0 or roi.shape[0] < 3 or roi.shape[1] < 5:
            return None

        best_text = None
        best_score = -1

        for scale in [3.0, 4.0]:
            processed = self._preprocess_white_threshold(roi, scale=scale)
            psm = '--psm 7' if mode == "alpha" else '--psm 7 -c tessedit_char_whitelist=0123456789'
            try:
                text = pytesseract.image_to_string(
                    processed, config=f'--oem 3 {psm}'
                ).strip()
                if text:
                    score = len(text)
                    if score > best_score:
                        best_score = score
                        best_text = text
            except Exception:
                pass

        return best_text

    def _preprocess_white_threshold(self, image: np.ndarray, scale: float = 3.0) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        return thresh

    def _preprocess_otsu(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def _preprocess_adaptive(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, -10
        )
        return thresh

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        return self._preprocess_white_threshold(image)

    def detect_player_tribe(self, frame: np.ndarray) -> str | None:
        """
        Auto-detect the player's tribe from the bottom status bar.
        The bar shows text like "City lvl 2 🏰 Imperius".
        """
        text = self.extract_text_alpha(frame, "tribe_bar")
        if not text:
            return None

        logger.debug(f"Tribe bar raw: '{text}'")

        # Clean and normalize the text
        cleaned = text.lower().strip()
        cleaned = re.sub(r'[^a-z\-]', ' ', cleaned)
        words = cleaned.split()

        # Match against known tribe names
        for word in words:
            for tribe in KNOWN_TRIBES:
                # Fuzzy match: allow 1-2 character differences for OCR errors
                if _fuzzy_match(word, tribe):
                    logger.info(f"Detected player tribe: {tribe} (from '{text}')")
                    return tribe

        logger.debug(f"Could not match tribe from: {words}")
        return None

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
                cleaned = re.sub(r'(\d),(\d)', r'\1\2', text)
                numbers = re.findall(r'\d+', cleaned)
                logger.debug(f"HUD numbers (cleaned): {numbers}")

                if len(numbers) >= 3:
                    stats["score"] = numbers[0]
                    stats["stars"] = numbers[1]
                    stats["turn"] = numbers[2]
                elif len(numbers) == 2:
                    stats["score"] = numbers[0]
                    stats["stars"] = numbers[1]
                elif len(numbers) == 1:
                    stats["score"] = numbers[0]

        if "hud_labels" in self.calibration.regions:
            label_text = self.extract_text_multi_strategy(frame, "hud_labels")
            if label_text:
                logger.debug(f"HUD labels raw: '{label_text}'")
                income_match = re.search(r'\+\s*(\d+)', label_text)
                if income_match:
                    stats["star_income"] = income_match.group(1)

        return stats


def _fuzzy_match(word: str, target: str, max_dist: int = 2) -> bool:
    """Check if word is within edit distance max_dist of target."""
    if word == target:
        return True
    if abs(len(word) - len(target)) > max_dist:
        return False
    # Simple character-level check: count matching characters
    matches = sum(1 for a, b in zip(word, target) if a == b)
    min_len = min(len(word), len(target))
    if min_len == 0:
        return False
    return matches >= min_len - max_dist
