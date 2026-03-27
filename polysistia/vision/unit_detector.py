import cv2
import numpy as np
import os

from ..state.models import UnitType, Unit, Position
from ..config import Calibration
from .grid_mapper import GridMapper

class UnitDetector:
    def __init__(self, calibration: Calibration, grid_mapper: GridMapper, templates_dir: str):
        self.calibration = calibration
        self.grid_mapper = grid_mapper
        self.templates_dir = templates_dir
        self.unit_templates = self._load_templates("units")

    def _load_templates(self, category: str) -> dict[str, np.ndarray]:
        templates = {}
        path = os.path.join(self.templates_dir, category)
        if not os.path.exists(path):
            return templates

        for filename in os.listdir(path):
            if filename.endswith(".png"):
                name = os.path.splitext(filename)[0]
                templates[name] = cv2.imread(os.path.join(path, filename))
        return templates

    def detect_units(self, frame: np.ndarray) -> list[Unit]:
        units = []
        for gx, gy in self.grid_mapper.get_all_visible_tiles():
            unit = self.get_unit_at(frame, gx, gy)
            if unit:
                units.append(unit)
        return units

    def get_unit_at(self, frame: np.ndarray, gx: int, gy: int) -> Unit | None:
        px, py = self.grid_mapper.get_tile_center(gx, gy)
        crop_size = 40
        y1, y2 = max(0, py - crop_size), min(frame.shape[0], py + crop_size)
        x1, x2 = max(0, px - crop_size), min(frame.shape[1], px + crop_size)
        unit_roi = frame[y1:y2, x1:x2]

        if unit_roi.size == 0:
            return None

        best_unit_type = None
        max_val = -1.0

        for name, template in self.unit_templates.items():
            if template.shape[0] > unit_roi.shape[0] or template.shape[1] > unit_roi.shape[1]:
                continue
            res = cv2.matchTemplate(unit_roi, template, cv2.TM_CCOEFF_NORMED)
            _, current_max, _, _ = cv2.minMaxLoc(res)
            if current_max > 0.8 and current_max > max_val:
                max_val = current_max
                try:
                    best_unit_type = UnitType(name)
                except ValueError:
                    pass

        if best_unit_type:
            tribe = self.detect_tribe(unit_roi)
            health = self.detect_health(unit_roi)
            return Unit(
                unit_type=best_unit_type,
                position=Position(x=gx, y=gy),
                owner_tribe=tribe,
                health=health
            )
        return None

    def detect_tribe(self, unit_roi: np.ndarray) -> str:
        from ..knowledge.tribes import tribe_knowledge
        hsv_roi = cv2.cvtColor(unit_roi, cv2.COLOR_BGR2HSV)

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

        return best_tribe if max_pixels > 10 else "unknown"

    def detect_health(self, unit_roi: np.ndarray) -> float:
        # Health bar is usually a green/red bar at the top or bottom of the unit sprite.
        # Simplified detection: look for green pixels in the ROI.
        hsv = cv2.cvtColor(unit_roi, cv2.COLOR_BGR2HSV)
        # Green health bar range
        lower_green = np.array([40, 50, 50])
        upper_green = np.array([80, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # Calculate ratio of green pixels to expected bar width
        green_pixels = cv2.countNonZero(mask)
        if green_pixels == 0:
            # Check for red (low health)
            lower_red = np.array([0, 50, 50])
            upper_red = np.array([10, 255, 255])
            mask_red = cv2.inRange(hsv, lower_red, upper_red)
            red_pixels = cv2.countNonZero(mask_red)
            if red_pixels > 0:
                return 0.1 # Very low
            return 1.0 # No bar visible, assume full health or unit just spawned

        # Simplified: max expected green pixels for a full bar is roughly 20-30 in a 40x40 ROI
        ratio = min(1.0, green_pixels / 25.0)
        return ratio
