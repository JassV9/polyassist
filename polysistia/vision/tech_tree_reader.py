import cv2
import numpy as np
import os

from ..config import Calibration

class TechTreeReader:
    def __init__(self, calibration: Calibration, templates_dir: str):
        self.calibration = calibration
        self.templates_dir = templates_dir
        self.tech_templates = self._load_templates("icons")

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

    def is_tech_tree_open(self, frame: np.ndarray) -> bool:
        """
        Detect if the tech tree screen is currently visible.
        In a real implementation, we would check for a UI landmark.
        """
        return False

    def get_researched_techs(self, frame: np.ndarray) -> list[str]:
        """
        When the tech tree screen is open, identify researched techs by color.
        Researched techs are colored/highlighted, unresearched are greyed out.
        """
        from ..knowledge.tech_tree import tech_tree
        researched = []
        if not self.is_tech_tree_open(frame):
            return researched

        # In a real implementation, we would have a mapping of tech names to icon pixel locations.
        # This is a placeholder that demonstrates the color-based logic.
        for tech_name in tech_tree.techs.keys():
            # icon_roi = frame[y:y+h, x:x+w]
            # if self._is_icon_colored(icon_roi):
            #     researched.append(tech_name)
            pass

        return researched

    def _is_icon_colored(self, icon_roi: np.ndarray) -> bool:
        # Check saturation. Greyscale icons have low saturation.
        hsv = cv2.cvtColor(icon_roi, cv2.COLOR_BGR2HSV)
        s_channel = hsv[:, :, 1]
        mean_s = np.mean(s_channel)
        return mean_s > 30 # Threshold for 'colored'
