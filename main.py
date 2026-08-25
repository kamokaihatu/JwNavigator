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
from widgets.settings_window import SettingsWindow
from utils.send_key import send_key_to_hwnd
from utils.send_command import send_command_to_hwnd, is_command_enabled, get_command_states
from utils import command_master
from utils.jww_watcher import get_raw_statusbar_text
from utils.state_parser import parse_statusbar_text
from utils.state_patterns import STATES_WITH_WAIT_RULE, is_hover_trustworthy_rule
from utils.state_collection import StateCollectionLogger
from utils.event_engine import JwwEventEngine
from utils.palette_layout import compute_palette_geometry

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
        self.settings_window = None
        self.last_jww_state = "STATE_IDLE"
        self.event_engines = {}  # 👑 ウィンドウ個別の安定判定エンジン管理辞書
        self.locked_intent = (
            {}
        )  # 👑 コマンド実行中の凹み上書き防止ロック（インテントホールド、値は(name, timestamp)）
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
    # 👑 送信直後の一瞬のIdle応答を吸収するためだけのロック。これより長く
    # 残すと、実際の状態と無関係に凹みが固定されたままになる（過去に
    # このロックを解除するコードが無く、永久に残ってしまうバグがあった）。
    LOCKED_INTENT_TTL_SEC = 1.5

    def _get_active_locked_intent(self, hwnd):
        entry = self.locked_intent.get(hwnd)
        if not entry:
            return None
        name, ts = entry
        if time.time() - ts > self.LOCKED_INTENT_TTL_SEC:
            del self.locked_intent[hwnd]
            return None
        return name

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
            jw_rect = get_jw_window_rect_safe(hwnd)
            screen_width = self.root.winfo_screenwidth()
            # 最大化時など、jw_cadの実際のウィンドウ矩形は見えない分の
            # リサイズ境界を含んで画面幅を超えることがある（Windowsの仕様）。
            # そのまま使うと右パレットが画面外にはみ出すため、実際の
            # モニター全体（マルチモニター含む仮想スクリーン）の範囲に
            # 収まるようクランプする（計算自体はutils/palette_layout側）。
            virtual_screen = (
                win32api.GetSystemMetrics(76),
                win32api.GetSystemMetrics(77),
                win32api.GetSystemMetrics(78),
                win32api.GetSystemMetrics(79),
            )
            # グループごとのボタン数が揃わないことがあるため、想定計算では
            # なくtoolbar自身が実際に作ったグループ数・一番長いグループの
            # ボタン数をそのまま渡す。
            def _side_info(tb):
                return {
                    "groups": tb.group_count(),
                    "max_group_len": tb.max_group_length(),
                    "button_count": len(tb.buttons),
                    "button_size": tb.button_size,
                    "orientation": tb.orientation,
                }
            left_info = _side_info(tl)
            right_info = _side_info(tr)
            geom = compute_palette_geometry(jw_rect, screen_width, virtual_screen, left_info, right_info)

            if not tl.is_pinned and geom["左"]:
                new_geom_l = geom["左"]
                # 位置が変わっていないのに毎回wm_geometry()を呼ぶと、
                # Windows側で「位置が更新された」扱いになり、意図せず
                # 最前面に上がってくることがある（実測で確認）。実際に
                # 変化があった時だけ呼ぶ。
                if getattr(tl, "_last_geom", None) != new_geom_l:
                    w, h, x, y = new_geom_l
                    tl.wm_geometry(f"{w}x{h}+{x}+{y}")
                    # wm_geometry()だけだと、他の操作（ボタン押下など）で
                    # イベントループが回るまで実際の描画に反映されないことが
                    # あるため、ここで強制的に反映させる。
                    tl.update_idletasks()
                    tl._last_geom = new_geom_l
            if not tr.is_pinned and geom["右"]:
                new_geom_r = geom["右"]
                if getattr(tr, "_last_geom", None) != new_geom_r:
                    w, h, x, y = new_geom_r
                    tr.wm_geometry(f"{w}x{h}+{x}+{y}")
                    tr.update_idletasks()
                    tr._last_geom = new_geom_r
            if foreground_hwnd in (hwnd, tl.winfo_id(), tr.winfo_id()):
                if len(tl.buttons) > 0:
                    tl.attributes("-topmost", True)
                if len(tr.buttons) > 0:
                    tr.attributes("-topmost", True)
            else:
                tl.attributes("-topmost", False)
                tr.attributes("-topmost", False)
        except Exception as e:
            self.write_system_log(f"❌ ウィンドウ同期エラー [HWND:{hwnd}]: {str(e)}")

    def _fast_sync_loop(self):
        # 👑 位置合わせ（sync_toolbar_position）だけをmonitor_loopの1秒周期から
        # 切り離し、こちらで高頻度に回す。jw_cadをドラッグしている最中でも
        # パレットが滑らかに追従できるようにするため。状態解析・ログ出力は
        # 重いのでmonitor_loop側の1秒周期のまま据え置く。
        if self._shutdown_requested:
            return
        for hwnd in list(self.active_launchers.keys()):
            try:
                self.sync_toolbar_position(hwnd)
            except Exception as e:
                self.write_system_log(f"❌ 高速位置同期エラー [HWND:{hwnd}]: {str(e)}")

        self._check_click_for_immediate_refresh()

        if not self._shutdown_requested:
            self.root.after(100, self._fast_sync_loop)

    def _check_click_for_immediate_refresh(self):
        # 👑 過去にクラッシュしたクリックフック（SetWindowsHookExWでOS側へ
        # コールバックを差し込む方式）とは別物。GetAsyncKeyStateはこちらから
        # 「前回確認してからクリックされたか」を聞きに行くだけの軽い呼び出しで、
        # コールバック注入がないため同種のクラッシュリスクはない。
        # jw_cadが前面にある時だけ、1秒周期を待たずその場で状態を読み直し、
        # 矩形の1点目のような短命な文言の取りこぼしを減らす。
        try:
            clicked = bool(win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x0001)
        except Exception:
            return
        if not clicked:
            return
        try:
            foreground_hwnd = win32gui.GetForegroundWindow()
        except Exception:
            return
        if foreground_hwnd not in self.active_launchers:
            return
        self.root.after(50, lambda h=foreground_hwnd: self._execute_pipeline_tick(h, time.perf_counter()))

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

                    def show_exit_popup(event, target_hwnd=hwnd):
                        menu = tk.Menu(self.root, tearoff=0, font=("Meiryo UI", 9))
                        menu.add_command(
                            label="⚙️ パレットを編集",
                            command=self.open_settings_window,
                        )
                        menu.add_separator()
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

    def reload_all_palettes(self):
        # 設定画面で保存した直後に呼ばれる。既存パレットを全部破棄して、
        # 「jw_cadが閉じた」時と同じ後始末をした上で、再スキャンして
        # config.jsonの最新内容から作り直させる。
        for hwnd in list(self.active_launchers.keys()):
            pair = self.active_launchers.pop(hwnd, None) or {}
            for tb in pair.values():
                try:
                    tb.destroy()
                except Exception:
                    pass
            self.event_engines.pop(hwnd, None)
            self.locked_intent.pop(hwnd, None)
        self.root.after(50, self._rebuild_palettes_now)

    def _rebuild_palettes_now(self):
        try:
            self._manage_palette_lifecycle(self.find_all_jw_cad_windows())
        except Exception as e:
            self.write_system_log(f"❌ パレット再構築失敗: {str(e)}")

    def open_settings_window(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return
        self.settings_window = SettingsWindow(self.root, manager_ref=self)

    def _update_button_enabled_states(self, hwnd, tl, tr):
        # jw_cad実ツールバーの有効/無効状態をまとめて調べ、対応するパレット
        # ボタンをグレーアウト/クリック無効化する。無効と判定できたものだけ
        # 反映し、判定不能（そのコマンドが今のツールバーに出ていない等）
        # なものは今まで通りクリック可能なままにする。
        try:
            id_map = {}
            for tb in (tl, tr):
                for btn in tb.buttons:
                    id_cmd = command_master.get_id_command(btn.command_key)
                    if id_cmd:
                        id_map[btn] = id_cmd
            if not id_map:
                return
            states = get_command_states(hwnd, set(id_map.values()))
            for btn, id_cmd in id_map.items():
                enabled = states.get(id_cmd)
                btn.set_enabled(enabled is not False)
        except Exception as e:
            self.write_system_log(f"❌ ボタン有効状態更新エラー [HWND:{hwnd}]: {str(e)}")

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

        self._update_button_enabled_states(hwnd, tl, tr)

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
                if self._get_active_locked_intent(hwnd):
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
                    # 次にIdle以外へ入った時、直前の状態を引きずらないように
                    # 安定判定エンジンもリセットしておく。
                    engine = self.event_engines.get(hwnd)
                    if engine:
                        engine.reset()
            else:
                # 👑 【2.0仕様：インテントロックが有効な場合は、そのインテントを優先】
                locked_name = self._get_active_locked_intent(hwnd)
                if locked_name:
                    match_keyword = locked_name
                else:
                    # 👑 パレット経由でないjw_cad側の直接操作は、マウスが他の
                    # ボタン上を通過/滞在した際のツールチップ文言を拾って
                    # しまうことがある（実測で確認）。追加の問い合わせは増やさず
                    # 次の2段構えで判定する:
                    #   ・入力待ち文言（WAIT系ルール）を持つコマンドは、マウスオン
                    #     だけでは絶対にその文言が出ない＝見えた瞬間に確定情報
                    #     として即時反映してよい（矩形の1点目のように、次の入力
                    #     ですぐ別の（未登録の）文言に変わるものもあるため、連続
                    #     一致を待つと取りこぼす）。ツールチップだけの間は反映しない。
                    #   ・WAIT文言が元々存在しないコマンド（複写・移動等）だけは、
                    #     今まで通りツールチップの2回連続一致で安定判定する。
                    jp_match_map = {
                        "LINE": "線",
                        "RECT": "矩形",
                        "CIRCLE": "円弧",
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

                    if current_state in STATES_WITH_WAIT_RULE:
                        if is_hover_trustworthy_rule(matched_rule):
                            reverse_btn_name = current_state.replace("STATE_", "")
                            match_keyword = jp_match_map.get(reverse_btn_name, None)
                        else:
                            match_keyword = None
                    else:
                        engine = self.event_engines.get(hwnd)
                        if engine is None:
                            engine = JwwEventEngine(required_matches=2)
                            self.event_engines[hwnd] = engine
                        engine.process_state(current_state)
                        stable_state = engine.stable_state
                        reverse_btn_name = stable_state.replace("STATE_", "")
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
            if is_command_enabled(hwnd, id_command) is False:
                self.write_system_log(
                    f"⚠️ [送信スキップ] jw_cad側で無効（グレーアウト）のため command_id={command_id} idCommand={id_command} を送信しませんでした。"
                )
                return
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
                            name = "面取" if btn.name in ["面取", "面取り"] else btn.name
                            self.locked_intent[hwnd] = (name, time.time())
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
        self.root.after(500, self._fast_sync_loop)
        self.root.after(30, self._drain_hook_queue)
        self.root.mainloop()


if __name__ == "__main__":
    manager = JwNavigatorManager()
    manager.start()
# ===== ✂️ main.py END PART 3 ✂️ =====
