# ===== ✂️ utils/send_command.py START ✂️ =====
import time

import win32con
import win32gui
import win32api

from utils.send_key import force_foreground_window

WM_COMMAND = 0x0111


def send_command_to_hwnd(hwnd: int, id_command: int) -> bool:
    if not hwnd or not id_command:
        return False

    if not win32gui.IsWindowEnabled(hwnd):
        return False

    force_foreground_window(hwnd)
    time.sleep(0.015)

    if not win32gui.IsWindowEnabled(hwnd):
        return False

    wparam = win32api.MAKELONG(id_command, 0)
    win32gui.PostMessage(hwnd, WM_COMMAND, wparam, 0)
    return True
# ===== ✂️ utils/send_command.py END ✂️ =====
