# ===== ✂️ tests/record_status_transitions.py START ✂️ =====
# Jw_cadのステータスバー文字列・マウス位置・クリック/ESCイベントを記録する収集ツール。
# JwNavigator本体（main.py）とは独立して動作させ、本体の実装には影響しない。
#
# 使い方:
#   1. Jw_cadを起動しておく
#   2. .venv/Scripts/python.exe tests/record_status_transitions.py を実行
#   3. data/_collector_control.txt に command_id（commands_master.csv参照。例: C001）を書き込む
#      （テキストエディタで直接編集してもよいし、他プロセスから書き込んでもよい）
#   4. Jw_cad側でそのコマンドを実際に操作する（ホバー・クリック・作業領域移動・ESCなど）
#   5. 以下のイベントが起きるたびに自動でCSVへ1行追記される
#        （MOVEは監視しない。フックコールバックの呼び出し頻度そのものが
#          クラッシュ頻度に直結していたため、クリック系のみに絞っている）
#        CLICK       : 左クリック直後（ボタン押下時）
#        CLICK_AFTER : 左クリックのボタン離し時
#        RCLICK      : 右クリック直後
#        RCLICK_AFTER: 右クリックのボタン離し時
#        ESC         : ESCキー押下時
#        AUTO        : 上記イベントを伴わずにステータスバー文字列だけが変化した場合
#   6. 次のコマンドに移るときは、また data/_collector_control.txt を書き換える
#   7. data/_collector_control.txt に QUIT と書き込むか Ctrl+C で終了
#
# ドラッグ操作は収集対象外（commands_master.md の方針通り）。
#
# ⚠️ 既知の不安定要素:
#   このマウス/キーボードフック機構（SetWindowsHookExW）は、実機検証で
#   Python 3.13.14環境において不定タイミングでネイティブクラッシュ
#   （_ctypes.pyd, 0xC000041D/0xC0000005）することを確認している
#   （詳細はJwNavigator本体main.pyのコメント参照）。
#   1イベントごとにCSVへ即時追記しているため、クラッシュしても収集済みの
#   行は失われない。落ちたらそのまま再実行して収集を続行すればよい。
#
# 出力: data/status_transitions.csv
#   (timestamp, command_id, event_type, x, y, raw_status_text)
import csv
import ctypes
from ctypes import wintypes
import datetime
import os
import queue
import sys
import threading
import time

import win32api
import win32con
import win32gui
import win32process

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.jww_watcher import get_raw_statusbar_text

JW_CAD_EXE_NAME = "jw_win.exe"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(REPO_ROOT, "data", "status_transitions.csv")
POLL_INTERVAL_SEC = 0.1

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


def _get_exe_name_for_hwnd(hwnd):
    handle = None
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid
        )
        path = win32process.GetModuleFileNameEx(handle, 0)
        return os.path.basename(path).lower()
    except Exception:
        return None
    finally:
        if handle:
            win32api.CloseHandle(handle)


def find_jw_cad_window():
    # 👑 タイトル文字列の部分一致ではなく、実行ファイル名（jw_win.exe）で厳密に判定する。
    # Explorerやエディタ等の無関係なウィンドウを誤って対象にしないため。
    found = []

    def enum_cb(hwnd, extra):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        if win32gui.GetParent(hwnd) != 0:
            return True
        if _get_exe_name_for_hwnd(hwnd) == JW_CAD_EXE_NAME:
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
        # 👑 フックコールバックはここへ積むだけにして、実処理（重いWin32呼び出し）は
        # 別スレッド（drain_hook_queue）で行う。ネイティブクラッシュ対策。
        self._hook_event_queue = queue.Queue()

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
        if x is not None and y is not None and not is_point_in_window(hwnd, x, y):
            return
        raw_text = get_raw_statusbar_text(hwnd)
        self._last_raw_text = raw_text
        self.append_row(event_type, x, y, raw_text)
        print(f"[{self.get_command_id() or '(未設定)'}] {event_type} ({x},{y}) {raw_text}")

    def drain_hook_queue(self):
        while True:
            try:
                event_type, x, y = self._hook_event_queue.get_nowait()
            except queue.Empty:
                break
            try:
                self.record_event(event_type, x, y)
            except Exception:
                pass

    def poll_loop(self):
        # 👑 マウス/キーボードイベントを伴わない自然な状態変化（AUTOモードの自動遷移等）を
        # 取りこぼさないための補助ポーリング。フックが積んだイベントもここで処理する
        # （ネイティブなフックコールバックの外で重い処理を行うことでクラッシュを避ける）。
        while self._running:
            self.drain_hook_queue()
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
            # 👑 ここでは座標をキューへ積むだけ。ウィンドウ列挙やSendMessage等の
            # 重いWin32呼び出しは絶対に行わない（ネイティブクラッシュ対策）。
            if nCode >= 0:
                try:
                    # 👑 WM_MOUSEMOVEは監視しない（システム全体で最高頻度のイベントであり、
                    # フックコールバックの呼び出し回数そのものがクラッシュ頻度に直結して
                    # いたため、実機検証でクリック系のみに絞ることにした）。
                    click_kind = {
                        WM_LBUTTONDOWN: "CLICK",
                        WM_LBUTTONUP: "CLICK_AFTER",
                        WM_RBUTTONDOWN: "RCLICK",
                        WM_RBUTTONUP: "RCLICK_AFTER",
                    }.get(wParam)
                    if click_kind:
                        data = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                        x, y = data.pt.x, data.pt.y
                        self.collector._hook_event_queue.put((click_kind, x, y))
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
                            self.collector._hook_event_queue.put(("ESC", None, None))
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


CONTROL_PATH = os.path.join(REPO_ROOT, "data", "_collector_control.txt")


def main():
    print("=== JwNavigator ステータスバー収集ツール ===")
    print(f"出力先: {OUTPUT_PATH}")
    print(f"制御ファイル: {CONTROL_PATH}")
    print(
        "このファイルに command_id（例: C001）を書き込むと自動的に切り替わります。"
        "'QUIT' と書き込むと終了します。"
    )
    print("マウス移動・クリック（左右）・ESCが自動記録されます。")

    collector = Collector()
    collector.ensure_csv_header()

    # 👑 起動直後の取りこぼし対策: poll_loop（別スレッド）を開始する前に、
    # 既に書かれているcommand_idを読み込んでおく（読み込み前にAUTO検知が
    # 走ってcommand_id未設定のまま記録されてしまうレースを防ぐ）。
    last_control = None
    if os.path.exists(CONTROL_PATH):
        with open(CONTROL_PATH, "r", encoding="utf-8") as f:
            last_control = f.read().strip()
        if last_control and last_control.upper() != "QUIT":
            collector.set_command_id(last_control)
            print(f"command_id -> {last_control}")

    poll_thread = threading.Thread(target=collector.poll_loop, daemon=True)
    poll_thread.start()

    hooks = InputHookController(collector)
    hooks.start()

    try:
        while True:
            time.sleep(0.5)
            if not os.path.exists(CONTROL_PATH):
                continue
            with open(CONTROL_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content == last_control:
                continue
            last_control = content
            if content.upper() == "QUIT":
                break
            collector.set_command_id(content)
            print(f"command_id -> {content or '(未設定)'}")
    except KeyboardInterrupt:
        pass
    finally:
        hooks.stop()
        collector.stop()
        print("収集を終了しました。")


if __name__ == "__main__":
    main()
# ===== ✂️ tests/record_status_transitions.py END ✂️ =====
