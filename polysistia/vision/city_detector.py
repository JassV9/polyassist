import cv2
import numpy as np
import re
import logging

from ..config import Calibration
from ..state.models import City, Position
from .ocr import OCR

logger = logging.getLogger(__name__)

# Official tribe colors from the Polytopia wiki, converted to BGR
TRIBE_COLORS_BGR = {
    "xin-xi":    (0, 0, 204),       # #cc0000
    "imperius":  (255, 0, 0),       # #0000ff
    "bardur":    (20, 37, 53),      # #352514
    "oumaji":    (0, 255, 255),     # #ffff00
    "kickoo":    (0, 255, 0),       # #00ff00
    "hoodrick":  (0, 102, 153),     # #996600
    "luxidoor":  (214, 59, 171),    # #ab3bd6
    "vengir":    (255, 255, 255),   # #ffffff
    "zebasi":    (0, 153, 255),     # #ff9900
    "ai-mo":     (170, 226, 54),    # #36e2aa
    "quetzali":  (74, 92, 39),      # #275c4a
    "yadakk":    (28, 35, 125),     # #7d231c
    "aquarion":  (129, 131, 243),   # #f38381
    "elyrion":   (153, 0, 255),     # #ff0099
    "polaris":   (133, 161, 182),   # #b6a185
    "cymanti":   (0, 253, 194),     # #c2fd00
}


class CityDetector:
    """
    Detects cities by finding white text clusters in the map area,
    then reading the colored background behind them to identify the tribe.
    """

    def __init__(self, calibration: Calibration, ocr: OCR):
        self.calibration = calibration
        self.ocr = ocr

    def detect_cities(self, frame: np.ndarray) -> list[City]:
        map_region = self.calibration.regions.get("map")
        if not map_region:
            logger.warning("No 'map' region in calibration")
            return []

        mx, my, mw, mh = map_region
        roi = frame[my:my+mh, mx:mx+mw]
        if roi.size == 0:
            return []

        banners = self._find_text_banners(roi)
        logger.debug(f"Found {len(banners)} candidate city banners")

        cities = []
        for (bx, by, bw, bh, bg_bgr) in banners:
            banner_roi = roi[by:by+bh, bx:bx+bw]

            name, population = self._read_banner_text(banner_roi)
            if not name:
                continue

            tribe = self._match_tribe_color(bg_bgr)

            abs_cx = mx + bx + bw // 2
            abs_cy = my + by + bh + 40

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
            logger.info(f"City: '{name}' ({tribe}) pop={population} at ({abs_cx},{abs_cy})")

        return cities

    def _find_text_banners(self, roi: np.ndarray) -> list[tuple[int, int, int, int, tuple]]:
        """
        Find city banners by looking for clusters of white text pixels
        that have a colored (non-terrain) background behind them.
        Returns list of (x, y, w, h, bg_bgr_tuple).
        """
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Step 1: Find bright white pixels (banner text is white)
        white_mask = (gray > 220).astype(np.uint8) * 255

        # Step 2: Group white pixels into text-like clusters
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (8, 4))
        text_groups = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
        kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 2))
        text_groups = cv2.morphologyEx(text_groups, cv2.MORPH_OPEN, kernel_open)

        contours, _ = cv2.findContours(text_groups, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        banners = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            # City name banners: 50-180px wide, 10-25px tall
            if w < 45 or w > 200 or h < 8 or h > 30:
                continue

            aspect = w / max(h, 1)
            if aspect < 2.0 or aspect > 10:
                continue

            # White pixel density must be high (banner text is dense)
            text_area = white_mask[y:y+h, x:x+w]
            white_density = cv2.countNonZero(text_area) / max(w * h, 1)
            if white_density < 0.15 or white_density > 0.7:
                continue

            # Step 3: Check the background color behind the white text
            pad = 4
            ey1 = max(0, y - pad)
            ey2 = min(roi.shape[0], y + h + pad)
            ex1 = max(0, x - pad)
            ex2 = min(roi.shape[1], x + w + pad)
            bg_region = roi[ey1:ey2, ex1:ex2]

            bg_gray = gray[ey1:ey2, ex1:ex2]
            bg_mask = (bg_gray < 180) & (bg_gray > 20)
            if np.sum(bg_mask) < 30:
                continue

            bg_pixels = bg_region[bg_mask]
            mean_bgr = tuple(bg_pixels.mean(axis=0).astype(int))

            # Step 4: Banner background must be a saturated tribe color
            hsv_bg = cv2.cvtColor(
                np.uint8([[list(mean_bgr)]]), cv2.COLOR_BGR2HSV
            )[0][0]

            # Require meaningful saturation (>50) -- rejects fog, terrain, gray UI
            # Exception: very dark colors (Bardur) with V < 60
            if hsv_bg[1] < 50 and hsv_bg[2] > 60:
                continue

            banners.append((x, y, w, h, mean_bgr))

        banners = self._merge_nearby(banners)
        return banners

    def _merge_nearby(self, banners):
        """Merge banners that are very close together."""
        if len(banners) <= 1:
            return banners

        banners = sorted(banners, key=lambda b: (b[1], b[0]))
        merged = [banners[0]]

        for b in banners[1:]:
            last = merged[-1]
            if (abs(b[0] - last[0]) < 30 and abs(b[1] - last[1]) < 20):
                # Merge into the larger one
                if b[2] * b[3] > last[2] * last[3]:
                    merged[-1] = b
            else:
                merged.append(b)

        return merged

    def _read_banner_text(self, banner_roi: np.ndarray) -> tuple[str | None, int]:
        """OCR the banner to extract city name and population."""
        text = self.ocr.ocr_roi(banner_roi, mode="alpha")
        if not text or len(text) < 2:
            return None, 0

        logger.debug(f"Banner raw text: '{text}'")

        population = 0
        name = text

        # Parse star population: "CityName ★N" or "CityName *N"
        pop_match = re.search(r'[\*\u2605xX#]\s*(\d+)', text)
        if pop_match:
            population = int(pop_match.group(1))
            name = text[:pop_match.start()].strip()

        if population == 0:
            trailing = re.search(r'\s+(\d+)\s*$', text)
            if trailing:
                population = int(trailing.group(1))
                name = text[:trailing.start()].strip()

        name = re.sub(r'[^a-zA-Z\s\-]', '', name).strip()
        if not name or len(name) < 4:
            return None, 0

        # Reject names that are mostly non-alphabetic noise
        alpha_ratio = sum(c.isalpha() for c in name) / max(len(name), 1)
        if alpha_ratio < 0.6:
            return None, 0

        return name, population

    def _match_tribe_color(self, bgr: tuple) -> str:
        """
        Match a BGR color against known tribe colors using HSV hue.
        Hue is robust to transparency/blending effects in-game.
        """
        from ..knowledge.tribes import tribe_knowledge

        pixel = np.uint8([[list(bgr)]])
        hsv = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)[0][0]
        hue, sat, val = int(hsv[0]), int(hsv[1]), int(hsv[2])

        best_tribe = "unknown"
        best_score = float('inf')

        for tribe_name, metadata in tribe_knowledge.tribes.items():
            lo = metadata.color_range_hsv[0]
            hi = metadata.color_range_hsv[1]

            # Check if the hue falls within the tribe's range
            h_lo, s_lo, v_lo = lo
            h_hi, s_hi, v_hi = hi

            h_center = (h_lo + h_hi) / 2
            h_dist = min(abs(hue - h_center), 180 - abs(hue - h_center))

            # Only consider if saturation is in reasonable range
            if sat < max(s_lo - 30, 0):
                continue

            if h_dist < best_score:
                best_score = h_dist
                best_tribe = tribe_name

        if best_score > 25:
            logger.debug(f"Banner HSV({hue},{sat},{val}) too far from any tribe (hue_dist={best_score:.0f})")
            return "unknown"

        return best_tribe
