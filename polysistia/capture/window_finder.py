import win32gui

import logging

logger = logging.getLogger(__name__)

def find_polytopia_window(title: str = "The Battle of Polytopia") -> tuple[int, int, int, int | None]:
    """
    Find the window with the given title and return its (x, y, w, h).
    """
    hwnd = win32gui.FindWindow(None, title)
    if not hwnd:
        logger.warning(f"Window with title '{title}' not found.")
        return None

    rect = win32gui.GetWindowRect(hwnd)
    x = rect[0]
    y = rect[1]
    w = rect[2] - x
    h = rect[3] - y

    return (x, y, w, h)

class WindowFinder:
    def __init__(self, title: str = "The Battle of Polytopia"):
        self.title = title

    def find(self) -> tuple[int, int, int, int | None]:
        return find_polytopia_window(self.title)
