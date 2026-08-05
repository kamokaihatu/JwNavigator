# ===== ✂️ utils/send_key.py START ✂️ =====
import ctypes
import time
import win32con
import win32gui
import win32process
import win32com.client

def force_foreground_window(hwnd: int) -> None:
    try:
        fore_hwnd = win32gui.GetForegroundWindow()
        if fore_hwnd == hwnd:
            return

        fore_thread, _ = win32process.GetWindowThreadProcessId(fore_hwnd)
        current_thread = ctypes.windll.kernel32.GetCurrentThreadId()

        ctypes.windll.user32.AttachThreadInput(current_thread, fore_thread, True)
        
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        win32gui.BringWindowToTop(hwnd)
        win32gui.SetForegroundWindow(hwnd)
        
        ctypes.windll.user32.AttachThreadInput(current_thread, fore_thread, False)
    except Exception:
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass

def send_key_to_hwnd(hwnd: int, key_str: str, mode: str = "A") -> None:
    if not hwnd or not key_str:
        return

    force_foreground_window(hwnd)
    time.sleep(0.015)

    try:
        shell = win32com.client.Dispatch("WScript.Shell")
    except Exception:
        return

    formatted_key = key_str.replace("{ESC}", "{ESCAPE}")

    if formatted_key.startswith("%"):
        sub_menu_char = formatted_key[2:]
        shell.SendKeys("%")
        time.sleep(0.03)
        shell.SendKeys("e")
        time.sleep(0.06)
        shell.SendKeys(sub_menu_char)
    else:
        shell.SendKeys(formatted_key)
# ===== ✂️ utils/send_key.py END ✂️ =====
