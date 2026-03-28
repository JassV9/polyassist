import win32gui

import logging

logger = logging.getLogger(__name__)

def find_polytopia_window(title: str = "The Battle of Polytopia") -> tuple[int, int, int, int] | None:
    """
    Find the window whose title contains the search string (case-insensitive)
    and return its (x, y, w, h).
    """
    # First try exact match (fast path)
    hwnd = win32gui.FindWindow(None, title)

    # Fall back to substring search across all windows
    if not hwnd:
        title_lower = title.lower()
        result = []

        def enum_cb(h, _):
            if win32gui.IsWindowVisible(h):
                window_text = win32gui.GetWindowText(h)
                if title_lower in window_text.lower():
                    result.append(h)

        win32gui.EnumWindows(enum_cb, None)
        if result:
            hwnd = result[0]
            logger.info(f"Found window via substring match: '{win32gui.GetWindowText(hwnd)}'")

    if not hwnd:
        logger.warning(f"No window matching '{title}' found.")
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

    def find(self) -> tuple[int, int, int, int] | None:
        return find_polytopia_window(self.title)
