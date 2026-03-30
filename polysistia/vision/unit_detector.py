import cv2
import numpy as np
import os
import logging

from ..state.models import UnitType, Unit, Position
from ..config import Calibration
from .grid_mapper import GridMapper
from ..knowledge.tribes import tribe_knowledge

logger = logging.getLogger(__name__)

# HSV ranges for health bar colors -- calibrated from actual game captures
# Actual measured health bar: HSV (56, 246, 182)
GREEN_HP_LOWER = np.array([48, 150, 140])
GREEN_HP_UPPER = np.array([82, 255, 255])
RED_HP_LOWER = np.array([0, 100, 100])
RED_HP_UPPER = np.array([10, 255, 255])
RED_HP_LOWER2 = np.array([170, 100, 100])
RED_HP_UPPER2 = np.array([180, 255, 255])

# Health bars: thin wide strips with strict shape constraints
MIN_HP_BAR_WIDTH = 8
MIN_HP_BAR_HEIGHT = 1
MAX_HP_BAR_HEIGHT = 7
MIN_HP_BAR_ASPECT = 2.5
MIN_HP_BAR_FILL = 0.3


class UnitDetector:
    def __init__(self, calibration: Calibration, grid_mapper: GridMapper, templates_dir: str):
        self.calibration = calibration
        self.grid_mapper = grid_mapper
        self.templates_dir = templates_dir
        self.unit_templates = self._load_templates("units")
        if self.unit_templates:
            logger.info(f"Loaded {len(self.unit_templates)} unit templates")
        else:
            logger.info("No unit templates found -- using color-based detection only")

    def _load_templates(self, category: str) -> dict[str, np.ndarray]:
        templates = {}
        path = os.path.join(self.templates_dir, category)
        if not os.path.exists(path):
            return templates

        for filename in os.listdir(path):
            if filename.endswith(".png"):
                name = os.path.splitext(filename)[0]
                img = cv2.imread(os.path.join(path, filename))
                if img is not None:
                    templates[name] = img
        return templates

    def detect_units(self, frame: np.ndarray) -> list[Unit]:
        """
        Primary detection: scan the map for green/red health bars.
        Each health bar indicates a unit. Fall back to template matching
        if templates are available for type classification.
        """
        map_region = self.calibration.regions.get("map")
        if not map_region:
            logger.warning("No 'map' region in calibration")
            return []

        mx, my, mw, mh = map_region
        map_roi = frame[my:my+mh, mx:mx+mw]
        if map_roi.size == 0:
            return []

        hp_bars = self._find_health_bars(map_roi)
        logger.debug(f"Found {len(hp_bars)} health bars in map")

        units = []
        for (hx, hy, hw, hh, health) in hp_bars:
            abs_x = mx + hx + hw // 2
            abs_y = my + hy + hh + 20  # unit sprite is below the HP bar

            tribe = self._detect_tribe_at(map_roi, hx, hy + hh, hw)
            unit_type = self._classify_unit(frame, abs_x, abs_y)

            unit = Unit(
                unit_type=unit_type,
                position=Position(x=abs_x, y=abs_y),
                owner_tribe=tribe,
                health=health,
            )
            units.append(unit)

        return units

    def _find_health_bars(self, roi: np.ndarray) -> list[tuple[int, int, int, int, float]]:
        """
        Scan for health bars (green and/or red horizontal strips).
        Returns list of (x, y, w, h, health_ratio).
        """
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        green_mask = cv2.inRange(hsv, GREEN_HP_LOWER, GREEN_HP_UPPER)
        red_mask1 = cv2.inRange(hsv, RED_HP_LOWER, RED_HP_UPPER)
        red_mask2 = cv2.inRange(hsv, RED_HP_LOWER2, RED_HP_UPPER2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)

        hp_mask = cv2.bitwise_or(green_mask, red_mask)

        # Morphological cleanup: connect nearby pixels horizontally
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
        hp_mask = cv2.morphologyEx(hp_mask, cv2.MORPH_CLOSE, kernel_h)
        hp_mask = cv2.morphologyEx(hp_mask, cv2.MORPH_OPEN,
                                    cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1)))

        contours, _ = cv2.findContours(hp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bars = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            if w < MIN_HP_BAR_WIDTH or h < MIN_HP_BAR_HEIGHT or h > MAX_HP_BAR_HEIGHT:
                continue

            aspect = w / max(h, 1)
            if aspect < MIN_HP_BAR_ASPECT:
                continue

            # Reject sparse contours -- health bars are solid filled rectangles
            area = cv2.contourArea(cnt)
            fill_ratio = area / max(w * h, 1)
            if fill_ratio < MIN_HP_BAR_FILL:
                continue

            # Determine health ratio from green vs red pixels in this bar
            bar_green = green_mask[y:y+h, x:x+w]
            bar_red = red_mask[y:y+h, x:x+w]
            green_px = cv2.countNonZero(bar_green)
            red_px = cv2.countNonZero(bar_red)
            total_px = green_px + red_px
            health = green_px / max(total_px, 1)

            bars.append((x, y, w, h, health))

        # Deduplicate bars that are very close together (within 20px)
        bars = self._deduplicate_bars(bars)
        return bars

    def _deduplicate_bars(self, bars: list[tuple[int, int, int, int, float]]) -> list[tuple[int, int, int, int, float]]:
        """Remove duplicate detections that are too close together."""
        if len(bars) <= 1:
            return bars

        bars = sorted(bars, key=lambda b: (b[1], b[0]))
        kept = [bars[0]]

        for bar in bars[1:]:
            bx, by = bar[0], bar[1]
            too_close = False
            for k in kept:
                kx, ky = k[0], k[1]
                if abs(bx - kx) < 20 and abs(by - ky) < 15:
                    too_close = True
                    break
            if not too_close:
                kept.append(bar)

        return kept

    def _detect_tribe_at(self, map_roi: np.ndarray, hx: int, below_y: int, bar_w: int) -> str:
        """
        Identify the tribe owning a unit by checking the colored base
        below the health bar.
        """
        base_y = below_y + 10
        base_h = 35
        base_x = max(0, hx - 10)
        base_w = bar_w + 20

        if (base_y + base_h > map_roi.shape[0] or
            base_x + base_w > map_roi.shape[1]):
            return "unknown"

        base_roi = map_roi[base_y:base_y+base_h, base_x:base_x+base_w]
        if base_roi.size == 0:
            return "unknown"

        hsv_roi = cv2.cvtColor(base_roi, cv2.COLOR_BGR2HSV)

        # Score each tribe by pixel count within its HSV range
        best_tribe = "unknown"
        max_pixels = 0

        for name, metadata in tribe_knowledge.tribes.items():
            lower = np.array(metadata.color_range_hsv[0])
            upper = np.array(metadata.color_range_hsv[1])
            mask = cv2.inRange(hsv_roi, lower, upper)
            count = cv2.countNonZero(mask)
            if count > max_pixels:
                max_pixels = count
                best_tribe = name

        # Require meaningful pixel count relative to ROI size
        min_pixels = max(10, base_h * base_w * 0.03)
        return best_tribe if max_pixels > min_pixels else "unknown"

    def _classify_unit(self, frame: np.ndarray, abs_x: int, abs_y: int) -> UnitType:
        """
        Try to classify the unit type using template matching if templates
        are available. Falls back to WARRIOR as the default type.
        """
        if not self.unit_templates:
            return UnitType.WARRIOR

        crop_size = 40
        y1 = max(0, abs_y - crop_size)
        y2 = min(frame.shape[0], abs_y + crop_size)
        x1 = max(0, abs_x - crop_size)
        x2 = min(frame.shape[1], abs_x + crop_size)
        unit_roi = frame[y1:y2, x1:x2]

        if unit_roi.size == 0:
            return UnitType.WARRIOR

        best_type = UnitType.WARRIOR
        max_val = 0.7  # minimum threshold for template match

        for name, template in self.unit_templates.items():
            if template.shape[0] > unit_roi.shape[0] or template.shape[1] > unit_roi.shape[1]:
                continue
            res = cv2.matchTemplate(unit_roi, template, cv2.TM_CCOEFF_NORMED)
            _, current_max, _, _ = cv2.minMaxLoc(res)
            if current_max > max_val:
                max_val = current_max
                try:
                    best_type = UnitType(name)
                except ValueError:
                    pass

        return best_type
