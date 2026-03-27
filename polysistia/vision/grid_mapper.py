import numpy as np

from ..config import Calibration

class GridMapper:
    def __init__(self, calibration: Calibration):
        self.origin = calibration.tile_grid.origin
        self.dx = calibration.tile_grid.dx
        self.dy = calibration.tile_grid.dy
        self.rows = calibration.tile_grid.rows
        self.cols = calibration.tile_grid.cols

    def pixel_to_tile(self, px: int, py: int) -> tuple[int, int]:
        """
        Convert pixel coordinates (px, py) to isometric grid coordinates (gx, gy).
        """
        # Center coordinates relative to the grid origin
        x_rel = px - self.origin[0]
        y_rel = py - self.origin[1]

        # Invert the isometric projection
        # gx = (x/dx + y/dy) / 2
        # gy = (y/dy - x/dx) / 2
        gx = round((x_rel / self.dx + y_rel / self.dy) / 2.0)
        gy = round((y_rel / self.dy - x_rel / self.dx) / 2.0)

        return int(gx), int(gy)

    def tile_to_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        """
        Convert isometric grid coordinates (gx, gy) to pixel coordinates (px, py).
        """
        # Forward isometric projection
        # x = (gx - gy) * dx
        # y = (gx + gy) * dy
        px = (gx - gy) * self.dx + self.origin[0]
        py = (gx + gy) * self.dy + self.origin[1]

        return int(px), int(py)

    def get_tile_center(self, gx: int, gy: int) -> tuple[int, int]:
        return self.tile_to_pixel(gx, gy)

    def get_all_visible_tiles(self) -> list[tuple[int, int]]:
        tiles = []
        for gx in range(self.rows):
            for gy in range(self.cols):
                tiles.append((gx, gy))
        return tiles
