# ===== ✂️ utils/send_key.py START ✂️ =====
import ctypes
import os
import time
import win32con
import win32gui
import win32process

# 👑 win32com.clientはimportされた瞬間にgencache（COM型情報のPythonラッパー
# キャッシュ）の生成先を決めるが、exe化した環境ではその既定パスが
# C:\WINDOWS\gen_py のような管理者権限が要る場所に解決されてしまうことが
# 実測で判明した（配布先の非管理者アカウントを想定したクリーン環境テストで
# PermissionErrorになり、main.pyの初期化全体が固まった。2026-08-31）。
# import win32com.client より前にキャッシュ先を各ユーザーが必ず書き込める
# %LOCALAPPDATA% 配下へ差し替えることで回避する。
import win32com
_gen_py_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "JwNavigator", "gen_py")
try:
    os.makedirs(_gen_py_dir, exist_ok=True)
    win32com.__gen_path__ = _gen_py_dir
except Exception:
    pass

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
