import os
import sys
import ctypes
from ctypes import wintypes
import tkinter as tk
import time
import datetime
import re
import threading
import queue
import logging

try:
    import win32gui
    import win32process
    import win32api
    import win32con
except ModuleNotFoundError as exc:
    raise SystemExit(
        "pywin32 のインポートに失敗しました。"
        f"実行中の Python: {sys.executable}\n"
        "次のコマンドで同じ Python 環境に pywin32 を入れてください:\n"
        f"{sys.executable} -m pip install pywin32"
    ) from exc

from widgets.toolbar import Toolbar
from utils.send_key import send_key_to_hwnd
from utils.send_command import send_command_to_hwnd
from utils import command_master
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
    except Exception as exc:
        logging.exception("main.py エラー")
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
            except Exception as exc:
                logging.exception("KeyboardHookController unhook failed")

            self._hook = None

    def _message_loop(self):
        callback_type = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_int, ctypes.c_uint, ctypes.c_long
        )

        @callback_type
        def hook_proc(nCode, wParam, lParam):
            # 👑 【0xC000041Dクラッシュ埋葬・第2弾】フックコールバック内では一切の重い処理
            # （ウィンドウ列挙・SendMessage等）を行わず、キューへ積むだけに徹する。
            if nCode >= 0 and getattr(self.manager, "state_collection_logger", None):
                try:
                    if wParam == WM_KEYDOWN:
                        vk_code = ctypes.cast(
                            lParam, ctypes.POINTER(ctypes.c_ulong)
                        ).contents.value
                        if vk_code == VK_ESCAPE:
                            self.manager.hook_event_queue.put(("ESC",))
                except Exception as exc:
                    logging.exception("KeyboardHookController unhook failed")

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
        except Exception as exc:
            logging.exception("KeyboardHookController unhook failed")

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
            except Exception as exc:
                logging.exception("MouseHookController unhook failed")

            self._hook = None

    def _message_loop(self):
        callback_type = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_int, ctypes.c_uint, ctypes.c_long
        )

        @callback_type
        def hook_proc(nCode, wParam, lParam):
            # 👑 【0xC000041Dクラッシュ埋葬・第2弾】フックコールバックの中でSendMessage等の
            # Win32同期呼び出しを行うと、低レベルフックのコールバック文脈として不安定になり
            # ネイティブクラッシュを招く。ここでは座標とイベント種別をキューへ積むだけに徹し、
            # 実際の重い処理（ステータスバー読み取り等）はTkinterのメインスレッド側
            # （_drain_hook_queue）で行う。
            if (
                nCode >= 0
                and getattr(self.manager, "state_collection_logger", None)
                and self.manager.state_collection_logger.is_enabled()
            ):
                try:
                    data = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                    x, y = data.pt.x, data.pt.y

                    if wParam == WM_MOUSEMOVE:
                        now = time.perf_counter()
                        if now - self._last_move_time >= 0.25:
                            self._last_move_time = now
                            self.manager.hook_event_queue.put(("MOVE", x, y))
                    elif wParam == WM_LBUTTONDOWN:
                        self.manager.hook_event_queue.put(("CLICK", x, y))
                    elif wParam == WM_LBUTTONUP:
                        self.manager.hook_event_queue.put(("CLICK_AFTER", x, y))
                except Exception as exc:
                    logging.exception("MouseHookController error")
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
        except Exception as exc:
            logging.exception("MouseHookController error")
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
        # 👑 フックコールバックはここへイベントを積むだけ。実処理はメインスレッドのdrainで行う。
        self.hook_event_queue = queue.Queue()

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
        self._auto_create_palettes = True
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

    JW_CAD_EXE_NAME = "jw_win.exe"

    @staticmethod
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

    def find_all_jw_cad_windows(self):
        # 👑 【誤検出完全埋葬】タイトル文字列の緩い部分一致（"jw"/"cad"含む等）は
        # Explorerやエディタ等の無関係なウィンドウにまでパレットを生成してしまう
        # 実害があったため廃止。実行ファイル名（jw_win.exe）による厳密一致のみを採用。
        jw_hwnds = []

        def enum_windows_callback(hwnd, extra):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                if win32gui.GetParent(hwnd) != 0:
                    return True
                exe_name = self._get_exe_name_for_hwnd(hwnd)
                if exe_name == self.JW_CAD_EXE_NAME:
                    jw_hwnds.append(hwnd)
            except Exception as exc:
                logging.exception("find_all_jw_cad_windows callback error")
            return True

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception as e:
            self.write_system_log(f"❌ EnumWindows失敗: {str(e)}")
        return jw_hwnds

    def find_jw_window_at_point(self, x, y):
        # 👑 マウスフック内から呼ばれるため、重いfind_all_jw_cad_windows()は使わず
        # 既知ウィンドウのキャッシュ（active_launchers）だけを参照する。
        for hwnd in list(self.active_launchers.keys()):
            try:
                left, top, right, bottom = get_jw_window_rect_safe(hwnd)
                if left <= x <= right and top <= y <= bottom:
                    return hwnd
            except Exception as exc:
                logging.exception("find_jw_window_at_point error")
        return None

    def capture_statusbar_for_window(self, hwnd):
        if not hwnd:
            return ""
        try:
            raw_text = get_raw_statusbar_text(hwnd)
            return raw_text.strip()
        except Exception as exc:
            logging.exception("capture_statusbar_for_window error")
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

    def _drain_hook_queue(self):
        # 👑 フック（別スレッド）が積んだイベントを、ここ（Tkinterメインスレッド）で
        # 安全に処理する。SendMessage等のWin32同期呼び出しはここでのみ行う。
        while True:
            try:
                event = self.hook_event_queue.get_nowait()
            except queue.Empty:
                break
            try:
                self._process_hook_event(event)
            except Exception:
                logging.exception("_drain_hook_queue processing error")
        if not self._shutdown_requested:
            self.root.after(30, self._drain_hook_queue)

    def _process_hook_event(self, event):
        kind = event[0]
        if kind == "ESC":
            known_hwnds = list(self.active_launchers.keys())
            raw_status_text = self.capture_statusbar_for_window(
                known_hwnds[0] if known_hwnds else None
            )
            self.record_state_collection_event(
                "ESC", "VK_ESCAPE", raw_status_text=raw_status_text
            )
            return

        event_type, x, y = kind, event[1], event[2]
        if not self.is_cursor_over_jw_window(x, y):
            return
        raw_status_text = self.capture_statusbar_for_point(x, y)
        self.record_state_collection_event(
            event_type, f"({x},{y})", raw_status_text=raw_status_text
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
            num_l = len(tl.buttons)
            num_r = len(tr.buttons)

            # 各列フレームにはドラッグ用の余白（padx/pady=3、widgets/toolbar.py
            # の_next_column_slot参照）が付いているため、その分をサイズ計算にも
            # 反映する。反映し忘れると右端の列がウィンドウ幅からはみ出す。
            COLUMN_PAD = 1

            def columns_and_height(count, max_rows):
                if count <= 0:
                    return 0, 0
                rows = min(count, max_rows) if max_rows > 0 else count
                cols = -(-count // max_rows) if max_rows > 0 else 1
                return cols, (rows * 52) + 52 + (COLUMN_PAD * 2)

            cols_l, tb_h_l = columns_and_height(num_l, tl.max_rows)
            cols_r, tb_h_r = columns_and_height(num_r, tr.max_rows)
            tb_w_l = cols_l * (52 + COLUMN_PAD * 2)
            tb_w_r = cols_r * (52 + COLUMN_PAD * 2)
            is_maximized = (
                x1 <= 0 and y1 <= 0 and jw_w >= self.root.winfo_screenwidth() - 20
            )
            if is_maximized:
                left_x = 0
                right_x = jw_w - tb_w_r - 16
                top_off = 70
            else:
                left_x = x1 - tb_w_l
                right_x = x2
                top_off = 0
            if not tl.is_pinned and num_l > 0:
                tl.wm_geometry(f"{tb_w_l}x{tb_h_l}+{left_x}+{y1 + top_off}")
            if not tr.is_pinned and num_r > 0:
                tr.wm_geometry(f"{tb_w_r}x{tb_h_r}+{right_x}+{y1 + top_off}")
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
                        execute_func=self.logged_execute_command,
                        manager_ref=self,
                    )
                    toolbar_r = Toolbar(
                        master=self.root,
                        side_type="右",
                        hwnd=hwnd,
                        execute_func=self.logged_execute_command,
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

    def logged_execute_command(self, hwnd, command_id):
        id_command = command_master.get_id_command(command_id)
        if id_command:
            self.write_system_log(
                f"【Jw送信】 source=palette target_hwnd={hwnd} command_id={command_id} idCommand={id_command}"
            )
            self.record_state_collection_event("SEND", command_id)
            sent = send_command_to_hwnd(hwnd, id_command)
            if not sent:
                self.write_system_log(
                    f"⚠️ [送信スキップ] ダイアログ等でメインウィンドウが無効なため command_id={command_id} を送信しませんでした。"
                )
                return
        else:
            shortcut_key = command_master.get_shortcut_key(command_id)
            if not shortcut_key:
                self.write_system_log(
                    f"⚠️ [送信不可] command_id={command_id} にidCommandもshortcut_keyも見つかりません。"
                )
                return
            self.write_system_log(
                f"【Jw送信】 source=palette target_hwnd={hwnd} command_id={command_id} key={shortcut_key}（フォールバック）"
            )
            self.record_state_collection_event("SEND", command_id)
            send_key_to_hwnd(hwnd, shortcut_key, mode="A")

        # 👑 【2.0仕様：ランチャー側クリック時は即座に先行点灯し、インテントをロック】
        for side_key in ["左", "右"]:
            if hwnd in self.active_launchers:
                tb = self.active_launchers[hwnd][side_key]
                for btn in tb.buttons:
                    if btn.command_key == command_id:
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
        # 👑 マウスフック内から呼ばれるため、重いfind_all_jw_cad_windows()は使わず
        # 既知ウィンドウのキャッシュ（active_launchers）だけを参照する。
        for hwnd in list(self.active_launchers.keys()):
            try:
                left, top, right, bottom = get_jw_window_rect_safe(hwnd)
                if left <= x <= right and top <= y <= bottom:
                    return True
            except Exception as exc:
                logging.exception("is_cursor_over_jw_window error")
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
        except Exception as exc:
            logging.exception("shutdown_manager after_cancel failed")
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
        self.write_system_log("▶️ 監視を開始します（パレット自動生成は有効・フックは無効）")
        # 👑 【0xC000041D根絶】この環境（Python 3.13.14 + pywin32）では、
        # SetWindowsHookExW(WH_MOUSE_LL/WH_KEYBOARD_LL)のctypesコールバックが
        # 実機のJw_cadウィンドウ操作中に不定タイミングでネイティブクラッシュ
        # （_ctypes.pyd, 0xC000041D/0xC0000005）することを実機検証で確認済み。
        # パレットのクリック送信・双方向連動（両想い）はフックに依存しないため、
        # 安定性を優先しフックは無効化している。クリック連動のホバー/クリック単位の
        # 状態収集が必要な場合は、原因を突き止めた上で再度有効化すること。
        # self.mouse_hook_controller.start()
        # self.keyboard_hook_controller.start()
        self._monitor_job = self.root.after(500, self.monitor_loop)
        self.root.after(30, self._drain_hook_queue)
        self.root.mainloop()


if __name__ == "__main__":
    manager = JwNavigatorManager()
    manager.start()
# ===== ✂️ main.py END PART 3 ✂️ =====
