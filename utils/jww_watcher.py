# ===== ✂️ utils/jww_watcher.py START ✂️ =====
import win32gui
import win32con
import ctypes

def get_raw_statusbar_text(main_hwnd: int) -> str:
    status_text = ""
    def enum_child_cb(hwnd, extra):
        nonlocal status_text
        if "statusbar" in win32gui.GetClassName(hwnd).lower():
            buffer = ctypes.create_unicode_buffer(256)
            length = win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, 256, ctypes.addressof(buffer))
            if length > 0:
                status_text = buffer.value.strip()
        return True
    win32gui.EnumChildWindows(main_hwnd, enum_child_cb, None)
    return status_text
# ===== ✂️ utils/jww_watcher.py END ✂️ =====
