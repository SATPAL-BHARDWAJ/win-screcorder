import ctypes
from PyQt5.QtWidgets import QDesktopWidget

try:
    import win32gui
    import win32con
    _WIN32 = True
except ImportError:
    _WIN32 = False


def enumerate_windows():
    """Return list of (hwnd, title) for all visible top-level windows."""
    results = []
    if not _WIN32:
        return results

    def _cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and title.strip():
                results.append((hwnd, title))

    win32gui.EnumWindows(_cb, None)
    return results


def get_window_rect(hwnd):
    """Return (x, y, w, h) for a window given its HWND. Returns None on failure."""
    if not _WIN32 or not hwnd:
        return None
    try:
        rect = win32gui.GetWindowRect(hwnd)
        x, y, x2, y2 = rect
        w, h = x2 - x, y2 - y
        if w <= 0 or h <= 0:
            return None
        return (x, y, w, h)
    except Exception:
        return None


def get_all_monitors_rect():
    """Return bounding rect (x, y, w, h) covering all connected monitors."""
    desk = QDesktopWidget()
    total = desk.geometry()
    for i in range(desk.screenCount()):
        total = total.united(desk.screenGeometry(i))
    return (total.x(), total.y(), total.width(), total.height())


def get_primary_monitor_rect():
    """Return (x, y, w, h) for the primary monitor."""
    desk = QDesktopWidget()
    primary = desk.screenGeometry(desk.primaryScreen())
    return (primary.x(), primary.y(), primary.width(), primary.height())
