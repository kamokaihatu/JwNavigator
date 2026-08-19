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
# ⚠️ 過去の実装（SetWindowsHookExWによるグローバルフック）について:
#   低レベルフックはシステム全体のマウス/キーボード入力を毎回このプロセスの
#   コールバック経由で通すため、フックが有効な間はシステム全体の入力が重くなり、
#   さらに実機検証でネイティブクラッシュ（_ctypes.pyd, 0xC000041D/0xC0000005）
#   が頻発することを確認した（MOVEを間引いても改善せず）。
#   そのため現在はOSフックを一切使わず、GetAsyncKeyStateによる定期ポーリング
#   （100ms間隔）でクリック/ESCを検出する方式に変更している。
#
# 出力: data/status_transitions.csv
#   (timestamp, command_id, event_type, x, y, raw_status_text)
import csv
import ctypes
import datetime
import os
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
CONTROL_PATH = os.path.join(REPO_ROOT, "data", "_collector_control.txt")
POLL_INTERVAL_SEC = 0.1

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02
VK_ESCAPE = 0x1B


def is_key_down(vk_code):
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)


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
        self._lbutton_down = False
        self._rbutton_down = False
        self._esc_down = False

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

    def _poll_input_state(self):
        lbtn = is_key_down(VK_LBUTTON)
        if lbtn != self._lbutton_down:
            self._lbutton_down = lbtn
            x, y = win32api.GetCursorPos()
            self.record_event("CLICK" if lbtn else "CLICK_AFTER", x, y)

        rbtn = is_key_down(VK_RBUTTON)
        if rbtn != self._rbutton_down:
            self._rbutton_down = rbtn
            x, y = win32api.GetCursorPos()
            self.record_event("RCLICK" if rbtn else "RCLICK_AFTER", x, y)

        esc = is_key_down(VK_ESCAPE)
        if esc and not self._esc_down:
            self.record_event("ESC")
        self._esc_down = esc

    def poll_loop(self):
        # 👑 OSフックを使わず、ここでボタン/キー状態とステータスバー文字列の両方を
        # ポーリングする。GetAsyncKeyStateはシステム全体の入力経路に割り込まないため、
        # フック方式で起きていたシステム全体の重さ・ネイティブクラッシュを回避できる。
        while self._running:
            try:
                self._poll_input_state()
            except Exception:
                pass
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


def main():
    print("=== JwNavigator ステータスバー収集ツール ===")
    print(f"出力先: {OUTPUT_PATH}")
    print(f"制御ファイル: {CONTROL_PATH}")
    print(
        "このファイルに command_id（例: C001）を書き込むと自動的に切り替わります。"
        "'QUIT' と書き込むと終了します。"
    )
    print("クリック（左右）・ESCが自動記録されます（100msポーリング）。")

    collector = Collector()
    collector.ensure_csv_header()

    # 👑 起動直後の取りこぼし対策: poll_loop（別スレッド）を開始する前に、
    # 既に書かれているcommand_idを読み込んでおく。
    last_control = None
    if os.path.exists(CONTROL_PATH):
        with open(CONTROL_PATH, "r", encoding="utf-8") as f:
            last_control = f.read().strip()
        if last_control and last_control.upper() != "QUIT":
            collector.set_command_id(last_control)
            print(f"command_id -> {last_control}")

    poll_thread = threading.Thread(target=collector.poll_loop, daemon=True)
    poll_thread.start()

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
        collector.stop()
        print("収集を終了しました。")


if __name__ == "__main__":
    main()
# ===== ✂️ tests/record_status_transitions.py END ✂️ =====
