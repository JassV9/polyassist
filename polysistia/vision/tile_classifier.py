import cv2
import numpy as np
import os

from ..state.models import TileType, ResourceType, Tile, Position
from ..config import Calibration
from .grid_mapper import GridMapper

class TileClassifier:
    def __init__(self, calibration: Calibration, grid_mapper: GridMapper, templates_dir: str):
        self.calibration = calibration
        self.grid_mapper = grid_mapper
        self.templates_dir = templates_dir
        self.tile_templates = self._load_templates("tiles")
        self.resource_templates = self._load_templates("resources")
        self.improvement_templates = self._load_templates("buildings")

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

    def classify_tile(self, frame: np.ndarray, gx: int, gy: int) -> Tile:
        px, py = self.grid_mapper.get_tile_center(gx, gy)

        # Crop region around the tile
        crop_size = 40
        y1, y2 = max(0, py - crop_size), min(frame.shape[0], py + crop_size)
        x1, x2 = max(0, px - crop_size), min(frame.shape[1], px + crop_size)
        tile_roi = frame[y1:y2, x1:x2]

        if tile_roi.size == 0:
            return Tile(position=Position(x=gx, y=gy), tile_type=TileType.GROUND)

        best_tile_type = TileType.GROUND
        max_val = -1.0

        for name, template in self.tile_templates.items():
            if template.shape[0] > tile_roi.shape[0] or template.shape[1] > tile_roi.shape[1]:
                continue
            res = cv2.matchTemplate(tile_roi, template, cv2.TM_CCOEFF_NORMED)
            _, current_max, _, _ = cv2.minMaxLoc(res)
            if current_max > max_val:
                max_val = current_max
                try:
                    best_tile_type = TileType(name)
                except ValueError:
                    pass

        best_resource = None
        max_res_val = -1.0
        for name, template in self.resource_templates.items():
            if template.shape[0] > tile_roi.shape[0] or template.shape[1] > tile_roi.shape[1]:
                continue
            res = cv2.matchTemplate(tile_roi, template, cv2.TM_CCOEFF_NORMED)
            _, current_max, _, _ = cv2.minMaxLoc(res)
            if current_max > 0.8 and current_max > max_res_val:
                max_res_val = current_max
                try:
                    best_resource = ResourceType(name)
                except ValueError:
                    pass

        return Tile(
            position=Position(x=gx, y=gy),
            tile_type=best_tile_type,
            resource=best_resource
        )

    def extract_all_tiles(self, frame: np.ndarray) -> list[Tile]:
        tiles = []
        for gx, gy in self.grid_mapper.get_all_visible_tiles():
            tiles.append(self.classify_tile(frame, gx, gy))
        return tiles
