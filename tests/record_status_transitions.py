# ===== ✂️ tests/record_status_transitions.py START ✂️ =====
# Jw_cadのステータスバー文字列・マウス位置・クリック/ESCイベントを記録する収集ツール。
# JwNavigator本体（main.py）とは独立して動作させ、本体の実装には影響しない。
#
# 使い方:
#   1. Jw_cadを起動しておく
#   2. .venv/Scripts/python.exe tests/record_status_transitions.py を実行
#   3. これからテストするコマンドの command_id（commands_master.csv参照。例: C001）を入力
#   4. Jw_cad側でそのコマンドを実際に操作する（ホバー・クリック・作業領域移動・ESCなど）
#   5. 以下のイベントが起きるたびに自動でCSVへ1行追記される
#        MOVE        : Jw_cadウィンドウ内でのマウス移動（250ms間隔で間引き）
#        CLICK       : 左クリック直後（ボタン押下時）
#        CLICK_AFTER : 左クリックのボタン離し時
#        RCLICK      : 右クリック直後
#        RCLICK_AFTER: 右クリックのボタン離し時
#        ESC         : ESCキー押下時
#        AUTO        : 上記イベントを伴わずにステータスバー文字列だけが変化した場合
#   6. 次のコマンドに移るときは、また command_id を入力し直す
#   7. quit または Ctrl+C で終了
#
# ドラッグ操作は収集対象外（commands_master.md の方針通り）。
#
# 出力: data/status_transitions.csv
#   (timestamp, command_id, event_type, x, y, raw_status_text)
import csv
import ctypes
from ctypes import wintypes
import datetime
import os
import sys
import threading
import time

import win32gui

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.jww_watcher import get_raw_statusbar_text

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(REPO_ROOT, "data", "status_transitions.csv")
POLL_INTERVAL_SEC = 0.1
MOVE_THROTTLE_SEC = 0.25

WH_MOUSE_LL = 14
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
VK_ESCAPE = 0x1B


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", ctypes.c_ulong),
        ("flags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


def find_jw_cad_window():
    # 👑 【本体からの独立方針】main.pyの厳密なパレット判定ロジックには依存せず、
    # 収集ツール単体で完結する簡易版のウィンドウ検出を持つ。
    found = []

    def enum_cb(hwnd, extra):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title_lower = win32gui.GetWindowText(hwnd).lower()
        if ("jw" in title_lower or "cad" in title_lower) and win32gui.GetParent(hwnd) == 0:
            found.append(hwnd)
        return True

    win32gui.EnumWindows(enum_cb, None)
    return found[0] if found else None


def get_window_rect_safe(hwnd):
    try:
        return win32gui.GetWindowRect(hwnd)
    except Exception:
        return None


def is_point_in_window(hwnd, x, y):
    rect = get_window_rect_safe(hwnd)
    if not rect:
        return False
    left, top, right, bottom = rect
    return left <= x <= right and top <= y <= bottom


class Collector:
    def __init__(self):
        self._current_command_id = ""
        self._lock = threading.Lock()
        self._running = True
        self._last_raw_text = None
        self._last_move_time = 0.0

    def set_command_id(self, command_id):
        with self._lock:
            self._current_command_id = command_id

    def get_command_id(self):
        with self._lock:
            return self._current_command_id

    def ensure_csv_header(self):
        if not os.path.exists(OUTPUT_PATH):
            os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
            with open(OUTPUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerow(
                    ["timestamp", "command_id", "event_type", "x", "y", "raw_status_text"]
                )

    def append_row(self, event_type, x, y, raw_text):
        with open(OUTPUT_PATH, "a", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow(
                [
                    datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    self.get_command_id(),
                    event_type,
                    x,
                    y,
                    raw_text,
                ]
            )

    def record_event(self, event_type, x=None, y=None):
        hwnd = find_jw_cad_window()
        if not hwnd:
            return
        raw_text = get_raw_statusbar_text(hwnd)
        self._last_raw_text = raw_text
        self.append_row(event_type, x, y, raw_text)
        print(f"[{self.get_command_id() or '(未設定)'}] {event_type} ({x},{y}) {raw_text}")

    def poll_loop(self):
        # 👑 マウス/キーボードイベントを伴わない自然な状態変化（AUTOモードの自動遷移等）を
        # 取りこぼさないための補助ポーリング。
        while self._running:
            hwnd = find_jw_cad_window()
            if hwnd:
                raw_text = get_raw_statusbar_text(hwnd)
                if raw_text != self._last_raw_text:
                    self._last_raw_text = raw_text
                    self.append_row("AUTO", None, None, raw_text)
                    print(f"[{self.get_command_id() or '(未設定)'}] AUTO {raw_text}")
            time.sleep(POLL_INTERVAL_SEC)

    def stop(self):
        self._running = False


class InputHookController:
    def __init__(self, collector: Collector):
        self.collector = collector
        self._mouse_hook = None
        self._keyboard_hook = None
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        for hook in (self._mouse_hook, self._keyboard_hook):
            if hook:
                try:
                    ctypes.windll.user32.UnhookWindowsHookEx(hook)
                except Exception:
                    pass
        self._mouse_hook = None
        self._keyboard_hook = None

    def _message_loop(self):
        callback_type = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_int, ctypes.c_uint, ctypes.c_long
        )

        @callback_type
        def mouse_proc(nCode, wParam, lParam):
            if nCode >= 0:
                try:
                    data = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                    x, y = data.pt.x, data.pt.y
                    hwnd = find_jw_cad_window()
                    if hwnd and is_point_in_window(hwnd, x, y):
                        if wParam == WM_MOUSEMOVE:
                            now = time.perf_counter()
                            if now - self.collector._last_move_time >= MOVE_THROTTLE_SEC:
                                self.collector._last_move_time = now
                                self.collector.record_event("MOVE", x, y)
                        elif wParam == WM_LBUTTONDOWN:
                            self.collector.record_event("CLICK", x, y)
                        elif wParam == WM_LBUTTONUP:
                            self.collector.record_event("CLICK_AFTER", x, y)
                        elif wParam == WM_RBUTTONDOWN:
                            self.collector.record_event("RCLICK", x, y)
                        elif wParam == WM_RBUTTONUP:
                            self.collector.record_event("RCLICK_AFTER", x, y)
                except Exception:
                    pass
            return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

        @callback_type
        def keyboard_proc(nCode, wParam, lParam):
            if nCode >= 0:
                try:
                    if wParam == WM_KEYDOWN:
                        vk_code = ctypes.cast(
                            lParam, ctypes.POINTER(ctypes.c_ulong)
                        ).contents.value
                        if vk_code == VK_ESCAPE:
                            self.collector.record_event("ESC")
                except Exception:
                    pass
            return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

        self._mouse_hook = ctypes.windll.user32.SetWindowsHookExW(
            WH_MOUSE_LL, mouse_proc, None, 0
        )
        self._keyboard_hook = ctypes.windll.user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, keyboard_proc, None, 0
        )
        msg = wintypes.MSG()
        while self._running:
            if ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))


def main():
    print("=== JwNavigator ステータスバー収集ツール ===")
    print(f"出力先: {OUTPUT_PATH}")
    print("これからテストする command_id（例: C001）を入力してから、Jw_cad側を操作してください。")
    print("マウス移動・クリック（左右）・ESCが自動記録されます。空Enterで command_id なし。")
    print("'quit' で終了します。")

    collector = Collector()
    collector.ensure_csv_header()

    poll_thread = threading.Thread(target=collector.poll_loop, daemon=True)
    poll_thread.start()

    hooks = InputHookController(collector)
    hooks.start()

    try:
        while True:
            command_id = input("command_id> ").strip()
            if command_id.lower() in ("quit", "exit"):
                break
            collector.set_command_id(command_id)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        hooks.stop()
        collector.stop()
        print("収集を終了しました。")


if __name__ == "__main__":
    main()
# ===== ✂️ tests/record_status_transitions.py END ✂️ =====
