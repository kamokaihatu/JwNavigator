import os
import sys
import ctypes
from ctypes import wintypes
import tkinter as tk
import time
import datetime
import re
import threading

try:
    import win32gui
except ModuleNotFoundError as exc:
    raise SystemExit(
        "pywin32 のインポートに失敗しました。"
        f"実行中の Python: {sys.executable}\n"
        "次のコマンドで同じ Python 環境に pywin32 を入れてください:\n"
        f"{sys.executable} -m pip install pywin32"
    ) from exc

from widgets.toolbar import Toolbar
from utils.send_key import send_key_to_hwnd
from utils.jww_watcher import get_raw_statusbar_text
from utils.state_parser import parse_statusbar_text
from utils.state_collection import StateCollectionLogger

WH_MOUSE_LL = 14
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
VK_ESCAPE = 0x1B


def get_jw_window_rect_safe(hwnd):
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return left, top, right, bottom
    except Exception:
        return 0, 0, 0, 0


class KeyboardHookController:
    def __init__(self, manager):
        self.manager = manager
        self._hook = None
        self._thread = None
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._hook:
            try:
                ctypes.windll.user32.UnhookWindowsHookEx(self._hook)
            except Exception:
                pass
            self._hook = None

    def _message_loop(self):
        callback_type = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_int, ctypes.c_uint, ctypes.c_long
        )

        @callback_type
        def hook_proc(nCode, wParam, lParam):
            if nCode >= 0 and getattr(self.manager, "state_collection_logger", None):
                try:
                    if wParam == WM_KEYDOWN:
                        vk_code = ctypes.cast(
                            lParam, ctypes.POINTER(ctypes.c_ulong)
                        ).contents.value
                        if vk_code == VK_ESCAPE:
                            raw_status_text = self.manager.capture_statusbar_for_window(
                                self.manager.find_all_jw_cad_windows()[0]
                                if self.manager.find_all_jw_cad_windows()
                                else None
                            )
                            self.manager.record_state_collection_event(
                                "ESC",
                                "VK_ESCAPE",
                                raw_status_text=raw_status_text,
                            )
                except Exception:
                    pass
            return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

        try:
            self._hook = ctypes.windll.user32.SetWindowsHookExW(
                WH_KEYBOARD_LL, hook_proc, None, 0
            )
            msg = wintypes.MSG()
            while self._running:
                if ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                    ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                    ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
        except Exception:
            pass
        finally:
            self.stop()


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", ctypes.c_ulong),
        ("flags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class MouseHookController:
    def __init__(self, manager):
        self.manager = manager
        self._hook = None
        self._thread = None
        self._running = False
        self._last_move_time = 0.0

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._hook:
            try:
                ctypes.windll.user32.UnhookWindowsHookEx(self._hook)
            except Exception:
                pass
            self._hook = None

    def _message_loop(self):
        callback_type = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_int, ctypes.c_uint, ctypes.c_long
        )

        @callback_type
        def hook_proc(nCode, wParam, lParam):
            if (
                nCode >= 0
                and getattr(self.manager, "state_collection_logger", None)
                and self.manager.state_collection_logger.is_enabled()
            ):
                try:
                    data = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                    x, y = data.pt.x, data.pt.y
                    inside_jw = self.manager.is_cursor_over_jw_window(x, y)

                    if inside_jw:
                        raw_status_text = self.manager.capture_statusbar_for_point(x, y)

                        if wParam == WM_MOUSEMOVE:
                            now = time.perf_counter()
                            if now - self._last_move_time >= 0.25:
                                self._last_move_time = now
                                self.manager.record_state_collection_event(
                                    "MOVE",
                                    f"({x},{y})",
                                    raw_status_text=raw_status_text,
                                )

                        elif wParam == WM_LBUTTONDOWN:
                            self.manager.record_state_collection_event(
                                "CLICK",
                                f"({x},{y})",
                                raw_status_text=raw_status_text,
                            )

                        elif wParam == WM_LBUTTONUP:
                            self.manager.record_state_collection_event(
                                "CLICK_AFTER",
                                f"({x},{y})",
                                raw_status_text=raw_status_text,
                            )
                except Exception:
                    pass

            return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

        try:
            self._hook = ctypes.windll.user32.SetWindowsHookExW(
                WH_MOUSE_LL, hook_proc, None, 0
            )
            msg = wintypes.MSG()
            while self._running:
                if ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                    ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                    ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
        except Exception:
            pass
        finally:
            self.stop()


class JwNavigatorManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.active_launchers = {}
        self.last_jww_state = "STATE_IDLE"
        self.event_engines = {}  # 👑 ウィンドウ個別の安定判定エンジン管理辞書
        self.locked_intent = (
            {}
        )  # 👑 コマンド実行中の凹み上書き防止ロック（インテントホールド）
        self.mouse_hook_controller = MouseHookController(self)
        self.keyboard_hook_controller = KeyboardHookController(self)

        # 👑 【リスト直撃クラッシュ完全埋葬】 sys.argvの0番目（文字列）を正確に参照してPath型エラーを防止
        script_path_str = sys.argv[0] if sys.argv else ""
        exe_dir = (
            os.path.dirname(os.path.abspath(script_path_str))
            if script_path_str
            else os.getcwd()
        )
        self.log_file_path = os.path.join(exe_dir, "JwNavigator_Log.txt")
        state_collection_log_path = os.path.join(
            exe_dir, "JwNavigator_StateCollection_Log.txt"
        )
        self.state_collection_logger = StateCollectionLogger(state_collection_log_path)
        self.state_collection_logger.enable()
        self._last_state_collection_state = None
        self._last_state_collection_rule = None
        self._shutdown_requested = False
        self._monitor_scheduled = False
        self._safe_mode = False
        self._auto_create_palettes = False
        self.root.withdraw()
        self.write_system_log("--- JwNavigator Ver2.0 メインシステム始動 ---")
        self.write_system_log("🧪 状態収集モードを有効化しました。")

    def write_system_log(self, text):
        now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(f"[{now_str}] {text}\n")
        except Exception as e:
            print(f"Log Write Error: {e}")

    def find_all_jw_cad_windows(self):
        jw_hwnds = []

        def enum_windows_callback(hwnd, extra):
            try:
                window_text = win32gui.GetWindowText(hwnd).lower()
                class_name = win32gui.GetClassName(hwnd).lower()
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                if (
                    "cabinetwclass" in class_name
                    or "jwnavigator" in window_text
                    or "visual studio" in window_text
                ):
                    jw_hwnds.append(hwnd)
                    return True
                if ("jw" in window_text or "cad" in window_text) and win32gui.GetParent(
                    hwnd
                ) == 0:
                    jw_hwnds.append(hwnd)
            except Exception:
                pass
            return True

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception as e:
            self.write_system_log(f"❌ EnumWindows失敗: {str(e)}")
        return jw_hwnds

    def find_jw_window_at_point(self, x, y):
        for hwnd in self.find_all_jw_cad_windows():
            try:
                left, top, right, bottom = get_jw_window_rect_safe(hwnd)
                if left <= x <= right and top <= y <= bottom:
                    return hwnd
            except Exception:
                pass
        return None

    def capture_statusbar_for_window(self, hwnd):
        if not hwnd:
            return ""
        try:
            raw_text = get_raw_statusbar_text(hwnd)
            return raw_text.strip()
        except Exception:
            return ""

    def capture_statusbar_for_point(self, x, y):
        hwnd = self.find_jw_window_at_point(x, y)
        return self.capture_statusbar_for_window(hwnd)

    def record_state_collection_event(
        self, event_type, detail, state=None, rule=None, raw_status_text=None
    ):
        if getattr(self, "state_collection_logger", None):
            self.state_collection_logger.record(
                event_type,
                detail,
                state=state,
                rule=rule,
                raw_status_text=raw_status_text,
            )

    # ===== ✂️ main.py START PART 2 ✂️ =====
    def sync_toolbar_position(self, hwnd):
        if hwnd not in self.active_launchers:
            return
        tl = self.active_launchers[hwnd]["左"]
        tr = self.active_launchers[hwnd]["右"]
        foreground_hwnd = win32gui.GetForegroundWindow()
        try:
            x1, y1, x2, y2 = get_jw_window_rect_safe(hwnd)
            jw_w = x2 - x1
            tb_w = 52
            num_l = len(tl.buttons)
            num_r = len(tr.buttons)
            tb_h_l = (num_l * 52) + 52 if num_l > 0 else 0
            tb_h_r = (num_r * 52) + 52 if num_r > 0 else 0
            is_maximized = (
                x1 <= 0 and y1 <= 0 and jw_w >= self.root.winfo_screenwidth() - 20
            )
            if is_maximized:
                left_x = 0
                right_x = jw_w - tb_w - 16
                top_off = 70
            else:
                left_x = x1 - tb_w
                right_x = x2
                top_off = 0
            if not tl.is_pinned and num_l > 0:
                tl.wm_geometry(f"{tb_w}x{tb_h_l}+{left_x}+{y1 + top_off}")
            if not tr.is_pinned and num_r > 0:
                tr.wm_geometry(f"{tb_w}x{tb_h_r}+{right_x}+{y1 + top_off}")
            if foreground_hwnd in (hwnd, tl.winfo_id(), tr.winfo_id()):
                if num_l > 0:
                    tl.attributes("-topmost", True)
                if num_r > 0:
                    tr.attributes("-topmost", True)
            else:
                tl.attributes("-topmost", False)
                tr.attributes("-topmost", False)
        except Exception as e:
            self.write_system_log(f"❌ ウィンドウ同期エラー [HWND:{hwnd}]: {str(e)}")

    def monitor_loop(self):
        if self._shutdown_requested:
            return
        t_loop_start = time.perf_counter()
        current_jw_hwnds = self.find_all_jw_cad_windows()
        if len(current_jw_hwnds) > 0:
            self.write_system_log(f"[監視] 検出HWND数={len(current_jw_hwnds)}")
        if self._auto_create_palettes:
            self._manage_palette_lifecycle(current_jw_hwnds)
            for hwnd in current_jw_hwnds:
                if hwnd in self.active_launchers:
                    self._execute_pipeline_tick(hwnd, t_loop_start)
        if not self._shutdown_requested:
            self._monitor_scheduled = True
            self.root.after(1000, self.monitor_loop)

    def _manage_palette_lifecycle(self, current_jw_hwnds):
        if not self._auto_create_palettes:
            return

        for hwnd in list(self.active_launchers.keys()):
            if hwnd not in current_jw_hwnds:
                if self.active_launchers[hwnd]["左"]:
                    self.active_launchers[hwnd]["左"].destroy()
                if self.active_launchers[hwnd]["右"]:
                    self.active_launchers[hwnd]["右"].destroy()
                del self.active_launchers[hwnd]
                if hwnd in self.event_engines:
                    del self.event_engines[hwnd]
                if hwnd in self.locked_intent:
                    del self.locked_intent[hwnd]
                self.write_system_log(
                    f"🧹 閉じられたJww [HWND:{hwnd}] のパレットを道連れ消滅させました。"
                )

        for hwnd in current_jw_hwnds:
            if hwnd not in self.active_launchers:
                try:
                    toolbar_l = Toolbar(
                        master=self.root,
                        side_type="左",
                        hwnd=hwnd,
                        send_key_func=self.logged_send_key,
                        manager_ref=self,
                    )
                    toolbar_r = Toolbar(
                        master=self.root,
                        side_type="右",
                        hwnd=hwnd,
                        send_key_func=self.logged_send_key,
                        manager_ref=self,
                    )
                    toolbar_l.status_label = tk.Label(
                        toolbar_l,
                        text="待機中",
                        font=("Meiryo UI", 7),
                        bg="#f0f0f0",
                        fg="#888888",
                    )
                    toolbar_l.status_label.pack(side="top", fill="x", pady=(0, 2))
                    self.enable_drag_move(toolbar_l)
                    self.enable_drag_move(toolbar_r)

                    def show_exit_popup(event, target_hwnd=hwnd):
                        menu = tk.Menu(self.root, tearoff=0, font=("Meiryo UI", 9))
                        menu.add_command(
                            label="⚙️ このパレットだけを閉じる",
                            command=lambda h=target_hwnd: self.close_single_palette(h),
                        )
                        menu.add_command(
                            label="❌ JwNaviシステムを終了する",
                            command=self.shutdown_manager,
                        )
                        menu.post(event.x_root, event.y_root)

                    toolbar_l.bind("<Button-3>", show_exit_popup)
                    toolbar_r.bind("<Button-3>", show_exit_popup)
                    if len(toolbar_l.buttons) > 0:
                        toolbar_l.deiconify()
                    else:
                        toolbar_l.deiconify()
                    if len(toolbar_r.buttons) > 0:
                        toolbar_r.deiconify()
                    else:
                        toolbar_r.deiconify()

                    self.active_launchers[hwnd] = {"左": toolbar_l, "右": toolbar_r}
                    self.root.update_idletasks()
                    toolbar_l.update_idletasks()
                    toolbar_r.update_idletasks()
                    self.write_system_log(
                        f"✨ 新規Jww [HWND:{hwnd}] を捕捉。双方向パレットをドッキングしました。"
                    )
                except Exception as e:
                    self.write_system_log(
                        f"❌ パレット動的構築失敗 [HWND:{hwnd}]: {str(e)}"
                    )

    # ===== ✂️ main.py END PART 2 ✂️ =====
    # ===== ✂️ main.py START PART 3 ✂️ =====
    def _execute_pipeline_tick(self, hwnd, t_loop_start):
        tl = self.active_launchers[hwnd]["左"]
        tr = self.active_launchers[hwnd]["右"]
        if hasattr(tl, "user_hidden") and tl.user_hidden:
            return

        if win32gui.IsIconic(hwnd):
            if tl.winfo_viewable():
                tl.withdraw()
            if tr.winfo_viewable():
                tr.withdraw()
            return
        else:
            if not tl.winfo_viewable() and len(tl.buttons) > 0:
                tl.deiconify()
            if not tr.winfo_viewable() and len(tr.buttons) > 0:
                tr.deiconify()

        self.sync_toolbar_position(hwnd)

        raw_text = get_raw_statusbar_text(hwnd)
        # 👑 【2.0仕様：ステータスバーテキストのクリーンアップ強化】
        # コマンド名に続く「（例：線）」のような情報を削除し、より厳密にコマンド名だけを抽出
        clean_raw_text = re.sub(r"[\s　]*[\(（][^）\)]*[\)）].*$", "", raw_text).strip()

        current_state, matched_rule = parse_statusbar_text(clean_raw_text)
        self.write_system_log(
            f"[状態解析] state={current_state} rule={matched_rule} raw={clean_raw_text}"
        )
        if (
            self._last_state_collection_state != current_state
            or self._last_state_collection_rule != matched_rule
        ):
            self.record_state_collection_event(
                "STATE", clean_raw_text, state=current_state, rule=matched_rule
            )
            self._last_state_collection_state = current_state
            self._last_state_collection_rule = matched_rule

        if hasattr(tl, "status_label"):
            if current_state == "STATE_IDLE":
                tl.status_label.configure(text="待機中", fg="#888888")
                if hwnd in self.locked_intent:
                    # コマンド送信直後は一時的に Idle を返しても、選択状態は維持する
                    if tl.current_selected_button:
                        tl.current_selected_button.set_selected()
                    if tr.current_selected_button:
                        tr.current_selected_button.set_selected()
                else:
                    # 実際に Idle に戻った時だけ、前回の選択状態を解除する
                    if tl.current_selected_button:
                        tl.current_selected_button.clear_selected()
                        tl.current_selected_button = None
                    if tr.current_selected_button:
                        tr.current_selected_button.clear_selected()
                        tr.current_selected_button = None
            else:
                # 👑 【2.0仕様：インテントロックが有効な場合は、そのインテントを優先】
                if hwnd in self.locked_intent:
                    match_keyword = self.locked_intent[hwnd]
                else:
                    # 👑 【β仕様：Jww状態の一瞬の切り替わり(TOOLTIP含む)を逃さず一対一ブリッジ】
                    # 後続の「始点を指示〜」の重複状態になっても、Idleに戻るまでは直前の凹みを維持
                    reverse_btn_name = current_state.replace("STATE_", "")

                    jp_match_map = {
                        "LINE": "線",
                        "RECT": "矩形",
                        "CIRCLE": "円",
                        "TEXT": "文字",
                        "DIM": "寸法",
                        "RANGE": "範囲",
                        "COPY": "複写",
                        "MOVE": "移動",
                        "DELETE": "消去",
                        "EXTEND": "伸縮",
                        "CORNER": "コーナー",
                        "CHAMFER": "面取",
                        "FILE_OPEN": "戻る",
                        "FILE_SAVE": "進む",
                    }

                    match_keyword = jp_match_map.get(reverse_btn_name, None)

                if match_keyword:
                    self.write_system_log(
                        f"[ボタン反映] 反映候補={match_keyword} state={current_state}"
                    )
                    for side_key in ["左", "右"]:
                        tb = self.active_launchers[hwnd][side_key]
                        for btn in tb.buttons:
                            # 👑 表記揺れを許容した厳密な完全一致判定
                            if btn.name == match_keyword or (
                                match_keyword == "面取" and btn.name == "面取り"
                            ):
                                self.write_system_log(
                                    f"[ボタン反映] 選択ボタン={btn.name} side={side_key}"
                                )
                                tb.select_button(btn)
                                break

    def logged_send_key(self, hwnd, key_str, mode="A"):
        self.write_system_log(
            f"【Jw送信】 source=palette target_hwnd={hwnd} key={key_str} mode={mode}"
        )
        self.record_state_collection_event("SEND", key_str)
        send_key_to_hwnd(hwnd, key_str, mode=mode)

        # 👑 【2.0仕様：ランチャー側クリック時は即座に先行点灯し、インテントをロック】
        for side_key in ["左", "右"]:
            if hwnd in self.active_launchers:
                tb = self.active_launchers[hwnd][side_key]
                for btn in tb.buttons:
                    if btn.command_key == key_str:
                        tb.select_button(btn)
                        # トグル動作でない機能を除外してインテントを先行ロック
                        if btn.name not in [
                            "戻る（アンドゥ）",
                            "進む（リドゥ）",
                            "戻る",
                            "進む",
                        ]:
                            self.locked_intent[hwnd] = (
                                "面取" if btn.name in ["面取", "面取り"] else btn.name
                            )
                        return

    def is_cursor_over_jw_window(self, x, y):
        for hwnd in self.find_all_jw_cad_windows():
            try:
                left, top, right, bottom = get_jw_window_rect_safe(hwnd)
                if left <= x <= right and top <= y <= bottom:
                    return True
            except Exception:
                pass
        return False

    def close_single_palette(self, hwnd):
        if hwnd in self.active_launchers:
            tl = self.active_launchers[hwnd]["左"]
            tr = self.active_launchers[hwnd]["右"]
            tl.user_hidden = True
            if tl:
                tl.destroy()
            if tr:
                tr.destroy()

    def shutdown_manager(self):
        if self._shutdown_requested:
            return
        self._shutdown_requested = True
        if self.mouse_hook_controller:
            self.mouse_hook_controller.stop()
        if self.keyboard_hook_controller:
            self.keyboard_hook_controller.stop()

        for hwnd in list(self.active_launchers.keys()):
            tl = self.active_launchers[hwnd]["左"]
            tr = self.active_launchers[hwnd]["右"]
            if tl:
                tl.destroy()
            if tr:
                tr.destroy()
        try:
            self.root.after_cancel(self._monitor_job)
        except Exception:
            pass
        self.root.quit()
        self.root.destroy()

    def enable_drag_move(self, window):
        import win32api

        def start_drag(event):
            window._drag_start_x, window._drag_start_y = event.x, event.y
            window.is_dragging = False

        def drag_motion(event):
            dx = event.x - window._drag_start_x
            dy = event.y - window._drag_start_y
            if abs(dx) > 3 or abs(dy) > 3:
                window.is_dragging = True
                if not window.is_pinned:
                    window.is_pinned = True
                    window.pin_btn.configure(text="自由", bg="#e1e1e1", relief="raised")

                tx = window.winfo_x() + dx
                ty = window.winfo_y() + dy
                wh = window.winfo_height()

                virtual_left = win32api.GetSystemMetrics(76)
                virtual_top = win32api.GetSystemMetrics(77)
                virtual_width = win32api.GetSystemMetrics(78)
                virtual_height = win32api.GetSystemMetrics(79)

                tx = max(virtual_left, min(tx, virtual_left + virtual_width - 52))
                ty = max(virtual_top, min(ty, virtual_top + virtual_height - wh))
                window.wm_geometry(f"+{tx}+{ty}")

        window.bind("<Button-1>", start_drag)
        window.bind("<B1-Motion>", drag_motion)

    def start(self):
        self.write_system_log("▶️ 監視を開始します（パレット自動生成は無効）")
        self.mouse_hook_controller.start()
        self.keyboard_hook_controller.start()
        self._monitor_job = self.root.after(500, self.monitor_loop)
        self.root.mainloop()


if __name__ == "__main__":
    manager = JwNavigatorManager()
    manager.start()
# ===== ✂️ main.py END PART 3 ✂️ =====
