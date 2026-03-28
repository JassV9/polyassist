import cv2
import numpy as np
import pytesseract
import re
import logging

from ..config import Calibration
from ..state.models import City, Position
from ..knowledge.tribes import tribe_knowledge

logger = logging.getLogger(__name__)

# Tribe banner colors in BGR (approximate, for distance matching).
# These are the dominant colors of the city name banners in-game.
TRIBE_BANNER_BGR = {
    "xin-xi": (40, 40, 200),
    "imperius": (200, 130, 50),
    "bardur": (50, 60, 120),
    "oumaji": (30, 180, 220),
    "kickoo": (180, 180, 30),
    "hoodrick": (30, 140, 30),
    "luxidoor": (180, 30, 180),
    "vengir": (40, 40, 40),
    "zebasi": (30, 200, 200),
    "ai-mo": (180, 30, 130),
    "quetzali": (80, 160, 50),
    "yaddak": (30, 100, 180),
    "aquarion": (200, 80, 30),
    "elyrion": (180, 50, 200),
    "polaris": (220, 220, 200),
    "cymanti": (40, 160, 80),
}


class CityDetector:
    """
    Detects cities by finding their name banners in the map area.
    City banners are colored rectangles with white text showing the
    city name and a star population indicator.
    """

    def __init__(self, calibration: Calibration):
        self.calibration = calibration
        pytesseract.pytesseract.tesseract_cmd = calibration.tesseract_cmd

    def detect_cities(self, frame: np.ndarray) -> list[City]:
        """Detect all city banners in the frame and return City objects."""
        map_region = self.calibration.regions.get("map")
        if not map_region:
            logger.warning("No 'map' region in calibration, scanning full frame")
            roi = frame
            offset_x, offset_y = 0, 0
        else:
            x, y, w, h = map_region
            roi = frame[y:y+h, x:x+w]
            offset_x, offset_y = x, y

        banners = self._find_banners(roi)
        logger.debug(f"Found {len(banners)} candidate city banners")

        cities = []
        for (bx, by, bw, bh) in banners:
            banner_roi = roi[by:by+bh, bx:bx+bw]
            name, population = self._read_banner_text(banner_roi)
            if not name:
                continue

            tribe = self._identify_tribe_from_banner(banner_roi)

            abs_cx = offset_x + bx + bw // 2
            abs_cy = offset_y + by + bh + 40  # city center is below the banner

            city = City(
                name=name,
                position=Position(x=abs_cx, y=abs_cy),
                owner_tribe=tribe,
                level=max(1, population),
                population=population,
                buildings=[],
                has_wall=False,
            )
            cities.append(city)
            logger.debug(f"City detected: {name} ({tribe}) pop={population} at ({abs_cx},{abs_cy})")

        return cities

    def _find_banners(self, roi: np.ndarray) -> list[tuple[int, int, int, int]]:
        """
        Find city name banners by looking for colored rectangles that
        contain white text. Returns list of (x, y, w, h) bounding boxes.
        """
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # City banners are saturated colored rectangles.
        # They typically have saturation > 40 and value > 60.
        # We also detect dark banners (Vengir) with low saturation but distinct shape.
        sat_mask = cv2.inRange(hsv, np.array([0, 40, 60]), np.array([180, 255, 255]))

        # Also include dark regions for tribes like Vengir
        dark_mask = cv2.inRange(hsv, np.array([0, 0, 20]), np.array([180, 30, 80]))
        combined_mask = cv2.bitwise_or(sat_mask, dark_mask)

        # Clean up with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        banners = []
        frame_h, frame_w = roi.shape[:2]

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            # City banners have a specific aspect ratio: wide and short
            aspect = w / max(h, 1)
            if aspect < 2.0 or aspect > 10.0:
                continue

            # Filter by size: banners are roughly 60-200px wide, 15-40px tall
            if w < 40 or w > 300 or h < 10 or h > 50:
                continue

            # Check that the banner interior has white text pixels
            banner_crop = gray[y:y+h, x:x+w]
            white_ratio = np.sum(banner_crop > 200) / max(banner_crop.size, 1)
            if white_ratio < 0.05:
                continue

            banners.append((x, y, w, h))

        # Merge overlapping banners
        banners = self._merge_overlapping(banners)
        return banners

    def _merge_overlapping(self, boxes: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
        """Merge overlapping bounding boxes."""
        if not boxes:
            return boxes

        boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
        merged = [boxes[0]]

        for bx, by, bw, bh in boxes[1:]:
            mx, my, mw, mh = merged[-1]
            if (bx < mx + mw and bx + bw > mx and
                by < my + mh and by + bh > my):
                # Merge
                nx = min(mx, bx)
                ny = min(my, by)
                nw = max(mx + mw, bx + bw) - nx
                nh = max(my + mh, by + bh) - ny
                merged[-1] = (nx, ny, nw, nh)
            else:
                merged.append((bx, by, bw, bh))

        return merged

    def _read_banner_text(self, banner_roi: np.ndarray) -> tuple[str | None, int]:
        """
        OCR the banner to extract city name and population.
        Returns (name, population). Population 0 means we couldn't read it.
        """
        if banner_roi.size == 0 or banner_roi.shape[0] < 5 or banner_roi.shape[1] < 10:
            return None, 0

        gray = cv2.cvtColor(banner_roi, cv2.COLOR_BGR2GRAY)
        scaled = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(scaled, 200, 255, cv2.THRESH_BINARY)

        try:
            text = pytesseract.image_to_string(thresh, config='--psm 7').strip()
        except Exception as e:
            logger.debug(f"Banner OCR failed: {e}")
            return None, 0

        if not text or len(text) < 2:
            return None, 0

        logger.debug(f"Banner raw text: '{text}'")

        # Parse: "CityName *N" or "CityName ★N" or just "CityName"
        # The star character is often misread as *, x, X, etc.
        population = 0
        name = text

        pop_match = re.search(r'[\*\u2605xX]\s*(\d+)', text)
        if pop_match:
            population = int(pop_match.group(1))
            name = text[:pop_match.start()].strip()

        # Also try just trailing digits
        if population == 0:
            trailing = re.search(r'\s+(\d+)\s*$', text)
            if trailing:
                population = int(trailing.group(1))
                name = text[:trailing.start()].strip()

        # Clean up the name: only keep alphabetic chars and spaces
        name = re.sub(r'[^a-zA-Z\s]', '', name).strip()
        if not name or len(name) < 2:
            return None, 0

        return name, population

    def _identify_tribe_from_banner(self, banner_roi: np.ndarray) -> str:
        """
        Determine which tribe owns a city by matching the banner's
        dominant color against known tribe colors.
        """
        if banner_roi.size == 0:
            return "unknown"

        # Mask out white text pixels to get just the banner background color
        gray = cv2.cvtColor(banner_roi, cv2.COLOR_BGR2GRAY)
        bg_mask = gray < 180  # non-text pixels

        if np.sum(bg_mask) < 10:
            return "unknown"

        mean_bgr = cv2.mean(banner_roi, mask=bg_mask.astype(np.uint8) * 255)[:3]

        best_tribe = "unknown"
        best_dist = float('inf')

        for tribe_name, ref_bgr in TRIBE_BANNER_BGR.items():
            dist = sum((a - b) ** 2 for a, b in zip(mean_bgr, ref_bgr)) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best_tribe = tribe_name

        # Only accept if the match is reasonably close
        if best_dist > 120:
            logger.debug(f"Banner color {mean_bgr} too far from any tribe (dist={best_dist:.0f})")
            return "unknown"

        return best_tribe
