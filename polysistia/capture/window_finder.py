import win32gui
import win32con

import logging

logger = logging.getLogger(__name__)


def _get_hwnd(title: str) -> int | None:
    """Find the window handle by exact match or substring search."""
    hwnd = win32gui.FindWindow(None, title)

    if not hwnd:
        title_lower = title.lower()
        result = []

        def enum_cb(h, _):
            if win32gui.IsWindowVisible(h):
                window_text = win32gui.GetWindowText(h).lower()
                if title_lower in window_text or window_text in title_lower:
                    result.append(h)

        win32gui.EnumWindows(enum_cb, None)
        if result:
            hwnd = result[0]
            logger.info(f"Found window via substring match: '{win32gui.GetWindowText(hwnd)}'")

    return hwnd if hwnd else None


def find_polytopia_window(title: str = "Polytopia") -> tuple[int, int, int, int] | None:
    """
    Find the Polytopia window and return its client-area (x, y, w, h).
    Returns None if the window is not found or is minimized.
    """
    hwnd = _get_hwnd(title)
    if not hwnd:
        logger.warning(f"No window matching '{title}' found.")
        return None

    if win32gui.IsIconic(hwnd):
        logger.info("Polytopia window is minimized, skipping.")
        return None

    placement = win32gui.GetWindowPlacement(hwnd)
    if placement[1] == win32con.SW_SHOWMINIMIZED:
        logger.info("Polytopia window is minimized (placement), skipping.")
        return None

    # Use client rect (excludes window border/shadow) mapped to screen coords
    client_rect = win32gui.GetClientRect(hwnd)
    left_top = win32gui.ClientToScreen(hwnd, (client_rect[0], client_rect[1]))
    right_bottom = win32gui.ClientToScreen(hwnd, (client_rect[2], client_rect[3]))

    x = left_top[0]
    y = left_top[1]
    w = right_bottom[0] - x
    h = right_bottom[1] - y

    if w <= 0 or h <= 0:
        logger.warning(f"Invalid client rect: ({x}, {y}, {w}, {h})")
        return None

    return (x, y, w, h)


def is_polytopia_foreground(title: str = "Polytopia") -> bool:
    """Check if the Polytopia window is the foreground (topmost visible) window."""
    hwnd = _get_hwnd(title)
    if not hwnd:
        return False
    return win32gui.GetForegroundWindow() == hwnd


class WindowFinder:
    def __init__(self, title: str = "Polytopia"):
        self.title = title

    def find(self) -> tuple[int, int, int, int] | None:
        return find_polytopia_window(self.title)

    def is_foreground(self) -> bool:
        return is_polytopia_foreground(self.title)
