from abc import ABC, abstractmethod
import numpy as np


class CaptureBackend(ABC):
    @abstractmethod
    def grab(self, region: tuple[int, int, int, int | None] = None) -> np.ndarray:
        """Capture screen region as BGR numpy array. None = full game window."""
        pass

    @abstractmethod
    def find_game_window(self) -> tuple[int, int, int, int | None]:
        """Return (x, y, w, h) of the Polytopia window, or None."""
        pass
