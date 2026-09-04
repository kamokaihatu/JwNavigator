import os
import sys
import signal
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import messagebox
import time
import datetime
import re
import threading
import queue
import logging
import uuid

try:
    import win32gui
    import win32process
    import win32api
    import win32con
    import win32event
    import winerror
except ModuleNotFoundError as exc:
    raise SystemExit(
        "pywin32 のインポートに失敗しました。"
        f"実行中の Python: {sys.executable}\n"
        "次のコマンドで同じ Python 環境に pywin32 を入れてください:\n"
        f"{sys.executable} -m pip install pywin32"
    ) from exc

# 👑 二重起動防止。exe化して配布すると「デスクトップのアイコンを
# ダブルクリックし忘れて連打する」等で2つ目が起動しやすくなる。同じ
# hwnd/config/ログファイルへ2プロセスが同時に触ると壊れるため、名前付き
# Mutexで検知し、2つ目は即座にメッセージを出して終了する（1つ目には
# 一切触らない — 最初に起動したプロセスをそのまま使ってもらう）。
_single_instance_mutex = win32event.CreateMutex(None, False, "JwNavigator_SingleInstance_Mutex")
if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
    try:
        ctypes.windll.user32.MessageBoxW(
            0,
            "JwNavigatorは既に起動しています。\nタスクトレイのアイコンをご確認ください。",
            "JwNavigator",
            0x40,  # MB_ICONINFORMATION
        )
    except Exception:
        pass
    sys.exit(0)

# 👑 DPI非対応のままだとWindowsがアプリ全体をビットマップ拡大表示する
# （DPI仮想化）。tkinterの自前描画ウィジェットはあまり目立たないが、
# ネイティブの共通ダイアログ（色選択等）はこの仮想化の影響をもろに受け、
# ウィンドウが極端に小さく・ボタンがほぼ見えない形で表示される（実測で
# 発覚：色選択ダイアログの「決定」ボタンがほぼ見えない）。tk.Tk()を
# 作る前にプロセスをDPI対応（Per-Monitor V2）にすることで解消する。
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from widgets.toolbar import Toolbar
from widgets.settings_window import SettingsWindow, TextInputDialog
from widgets.first_launch_dialog import run_first_launch_setup_if_needed, run_preset_reset
from utils.send_key import send_key_to_hwnd
from utils.send_command import send_command_to_hwnd, is_command_enabled, get_command_states, get_command_checked_states, get_command_pressed_states
from utils import line_attr_dialog
from utils import command_master
from utils.jww_watcher import get_raw_statusbar_text
from utils.state_parser import parse_statusbar_text
from utils.state_patterns import is_hover_trustworthy_rule
from utils.state_collection import StateCollectionLogger
from utils.win_event_watcher import WinEventWatcher
from utils.palette_layout import compute_palette_geometry
from utils import window_state
from utils import auto_attr_state
from utils import menu_prefs
from utils import palette_config
from utils import layer_snapshot
from utils.tray_icon import TrayIcon

WH_MOUSE_LL = 14
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
VK_ESCAPE = 0x1B

# 👑 jw_cad直接操作 → パレット反映のための、state_id(STATE_*からSTATE_を
# 除いたもの)からボタン表示名への対応表。以前はここに左パレットの14個分
# しか登録されておらず、右パレットの22個は最初から一つも反映されていな
# かった（2026-08-26発覚）。utils/state_patterns.pyのSTATE_DATABASEに
# 実測データがある範囲で、config.jsonに現在設定されている全ボタン分を
# 網羅している。ソリッド（C018）だけは対応する状態が未実測のため未対応。
# 戻る/進むは以前「FILE_OPEN」「FILE_SAVE」という無関係な状態にひもづく
# 場当たり的な対応になっていたため、本来のMODORU/SUSUMUに訂正した。
JP_MATCH_MAP = {
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
    "MODORU": "戻る",
    "SUSUMU": "進む",
    "BLOCK_KA": "Blk化",
    "BLOCK_KAI": "Blk解",
    "BLOCK_HEN": "Blk編",
    "POINT": "点",
    "CENTER": "中心線",
    "RENTENT": "連続線",
    "SESSEN": "接線",
    "SETSUEN": "接円",
    "HATCH": "ハッチ",
    "POLYGON": "多角形",
    "CURVE": "曲線",
    "SOLID": "ソリッド",
    "FUKUSEN": "複線",
    "BUNKATSU": "分割",
    "CLEANUP": "整理",
    "FILE_SAVE_OVER": "上書",
    "PRINT": "印刷",
    "FILE_SAVE_AS": "保存",
    "CLIP_COPY": "コピー",
    "HARITSUKE": "貼付",
    "CHUSHIN_TEN": "中心点",
    "ENSHU_4TEN": "円周1/4点",
    "SOKUTEI": "測定",
    "ZOKUSEI_SHUTOKU": "属性取得",
    "NITEN_CHO": "2点長",
}


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
        # 👑 config/config.jsonがまだ無ければ初回起動とみなし、パレットの
        # 初期構成（空/ミニマム/jw初期/開発者おすすめ/フル）を選ばせる。
        # 以降のパレット構築・監視系のセットアップより前、ここで確実に
        # 一度だけ行う（config.jsonが既にあれば即座に何もせず戻る）。
        run_first_launch_setup_if_needed(self.root)
        self.active_launchers = {}
        # 👑 「補助線のまま再起動かかって、直線から始まったときに補助線
        # 属性になっちゃう」への対応。JwNavigator自体が(開発中の再起動や
        # クラッシュ等で)補助線モードの途中で終了しても、jw_cadは別
        # プロセスとして補助線色/線種のまま動き続ける。前回終了時点の
        # originalをここで読み直しておくことで、次に対象コマンドから
        # 離脱した時に正しい「元の線属性」へ戻せるようにする(trigger_btn
        # は再起動後まだウィジェットが無いのでNoneのまま。_revert_auto_attr
        # 側は既にtrigger_btnがNoneでも動く作りになっている)。
        self._auto_attr_pending = {
            hwnd: {**entry, "trigger_btn": None}
            for hwnd, entry in auto_attr_state.load_pending().items()
        }  # hwnd -> {"original": {...}, "confirmed": bool}
        # 👑 「見本で選ぶ…」の直近の読み込み結果を覚えておく受動的キャッシュ
        # ({"data": ...}の共有可変dict)。バックグラウンド先読みは行わない
        # (ユーザーが読み込みボタンを押した時だけ書き込まれる)。以前は
        # SettingsWindow側だけで保持していたため、設定画面を閉じて開き
        # 直すたびにキャッシュが消えていた(「2回目に線属性設定するとき、
        # 見本から選ぶがキャッシュされてないよ」)。app全体で持つことで
        # 設定画面を開き直しても前回の読み込み結果を使い回せる。
        self.swatch_cache = {"data": None}
        # 👑 レイヤ保存ボタン: Ctrl+<キー>送出でA_SAVE.bat起動後、ユーザーが
        # 範囲選択→確定を終えてLAYER_RESTORE.JWLが更新されるのを待つ状態。
        # hwnd -> {"pending": layer_snapshot.trigger_save()の戻り値,
        #          "dest_path": .., "started_at": time.time(), "button": entry}
        self._pending_layer_saves = {}
        self.settings_window = None
        self.last_jww_state = "STATE_IDLE"
        self.event_engines = {}  # 👑 ウィンドウ個別の安定判定エンジン管理辞書
        self.locked_intent = (
            {}
        )  # 👑 コマンド実行中の凹み上書き防止ロック（インテントホールド、値は(name, timestamp)）
        self.mouse_hook_controller = MouseHookController(self)
        self.keyboard_hook_controller = KeyboardHookController(self)
        self.win_event_watcher = WinEventWatcher()
        self._win_event_watch_pids = {}  # hwnd -> pid（unwatch時に使う）
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
        # 👑 開発中はパターン収集のため常時有効にしていたが、配布後は
        # コマンド送信のたびにディスクへ書き込むだけの負荷になるため、
        # 既定で無効にした。トレイメニューの「詳細ログを有効にする」で
        # 必要な時だけONにする運用に変更（配布向け運用設計）。
        self._last_state_collection_state = None
        self._last_state_collection_rule = None
        self._shutdown_requested = False
        self._monitor_scheduled = False
        self._safe_mode = False
        self._auto_create_palettes = True
        self.window_state = window_state.load_state()
        self._pending_pin_restore = {}
        self.tray_icon = None
        self.root.withdraw()
        self.write_system_log("--- JwNavigator Ver3.60 メインシステム始動 ---")

    LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB

    def write_system_log(self, text):
        now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            self._rotate_log_if_needed(self.log_file_path)
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(f"[{now_str}] {text}\n")
        except Exception as e:
            print(f"Log Write Error: {e}")

    def _rotate_log_if_needed(self, path):
        # 👑 配布後は開発時と違って無制限に増え続けても誰も気づかないため、
        # 一定サイズを超えたら古い前半を切り捨てる簡易ローテーション。
        # 不具合報告時にログをコピペしてもらう運用は残したいので、
        # 完全に消さず直近分は必ず残す。
        try:
            if os.path.getsize(path) <= self.LOG_MAX_BYTES:
                return
        except OSError:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            keep = lines[len(lines) // 2:]
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(keep)
        except Exception:
            pass

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
                # 👑 jw_cadのタイトルバーを右クリックすると出るWindowsシステム
                # メニュー（閉じる/最大化等）は、class="#32768"・title=""・
                # GetParent()==0・所属exeがjw_win.exeという、既存条件を
                # すり抜けてしまう一時ウィンドウとして一瞬だけ出現することを
                # SetWinEventHook(EVENT_SYSTEM_MENUPOPUPSTART)で実測確認
                # （2026-08-31、ユーザー報告）。その間だけ丸ごと新しい図面と
                # 誤認識してパレット一式を作っては、メニューが閉じると同時に
                # 消える、という不具合になっていた。実際の図面ウィンドウは
                # 必ず「ファイル名 - jw_win」のタイトルを持つので、空タイトル
                # で弾けば区別できる。
                if not win32gui.GetWindowText(hwnd):
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
            # 👑 【重大発覚】tl.winfo_id()/tr.winfo_id()は実は「本当の
            # トップレベルウィンドウ」ではなく、その内側の子ウィンドウの
            # hwndを返していた（実測でGetParent()!=0を確認、実際の
            # TkTopLevelはさらにその親）。今日一日SetWindowPosの結果が
            # 左右非対称・不安定だったのはこれが原因で、子ウィンドウの
            # 兄弟内Z順をいじっていただけで、jw_cad等の他トップレベル
            # ウィンドウとの前後関係には実質影響していなかった。実際に
            # Z順操作すべきは GetParent(winfo_id()) で辿れる本当の
            # トップレベルhwnd（一度だけ取得してキャッシュする）。
            #
            # 「常にjw_cad本体の一個だけ前面」に固定する方式。
            # SetWindowPos(hWndInsertAfter=X)は「Xの直後＝Xより後ろ（背面側）」
            # に置く動きだと実測で確定した（hWndInsertAfter=hwndを試したところ
            # 常にjw_cad本体より背面になった）。そこで逆に、「今現在jw_cad
            # 本体の直前（１つ前面）にいるウィンドウ」をGW_HWNDPREVで探し、
            # その一つ後ろにパレットを割り込ませることで「本体の直前」を作る。
            # 自分自身（左右パレット）が既にそこにいる場合は無視して更に
            # 上を探す（毎tick呼ぶ想定で、既に自分が挟まっている状態を
            # 誤って自分の後ろに付けようとする自己参照を避けるため）。
            # jw_cad自身が出すダイアログ（文字ツールバー等）は新規作成時に
            # 通常Z順の最前面へ自動挿入される仕様なので、この「本体の直前」
            # より必ず前に来る。他アプリ（VSCode等）がアクティブになれば
            # jw_cad本体ごと後ろへ下がるのでパレットも一緒に下がる。
            def _real_top_level_hwnd(tb):
                cached = getattr(tb, "_real_hwnd", None)
                if cached:
                    return cached
                inner = tb.winfo_id()
                parent = win32gui.GetParent(inner)
                real = parent if parent else inner
                tb._real_hwnd = real
                return real

            def _neighbor_above(target_hwnd, exclude_ids):
                cur = win32gui.GetWindow(target_hwnd, win32con.GW_HWNDPREV)
                while cur and cur in exclude_ids:
                    cur = win32gui.GetWindow(cur, win32con.GW_HWNDPREV)
                return cur

            palette_real_ids = {_real_top_level_hwnd(tl), _real_top_level_hwnd(tr)}
            for tb, side_label in ((tl, "左"), (tr, "右")):
                if len(tb.buttons) == 0:
                    continue
                if not getattr(tb, "_topmost_cleared", False):
                    tb.attributes("-topmost", False)
                    tb._topmost_cleared = True
                try:
                    real_hwnd = _real_top_level_hwnd(tb)
                    neighbor = _neighbor_above(hwnd, palette_real_ids)
                    insert_after = neighbor if neighbor else win32con.HWND_TOP
                    win32gui.SetWindowPos(
                        real_hwnd, insert_after, 0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
                    )
                except Exception as e:
                    self.write_system_log(f"⚠️ {side_label}パレットZ順変更エラー: {str(e)}")
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
        self.root.after(
            50,
            lambda h=foreground_hwnd: self._execute_pipeline_tick(h, time.perf_counter(), click_confirmed=True),
        )

    def monitor_loop(self):
        if self._shutdown_requested:
            return
        t_loop_start = time.perf_counter()
        self._check_pending_layer_saves()
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
                self._auto_attr_pending.pop(hwnd, None)
                auto_attr_state.save_pending(self._auto_attr_pending)
                pid = self._win_event_watch_pids.pop(hwnd, None)
                if pid:
                    self.win_event_watcher.unwatch_pid(pid)
                # 👑 「jwを再起動するまではキャッシュ保持しといてほしい」。
                # jw_cadが閉じられた(=再起動されうる)タイミングで見本
                # キャッシュを破棄し、次にjw_cadが起動して「見本で選ぶ…」を
                # 使う時は改めて実物を読み取り直す(基本設定が変わっている
                # 可能性があるため)。
                self.swatch_cache["data"] = None
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

                    def show_exit_popup(event, target_hwnd=hwnd, side_key="左"):
                        # 👑 「⚙️ 編集」だけは常に表示（消せない）。それ以外は
                        # 設定画面の「右クリック」タブでON/OFFできる
                        # (ユーザー要望: 普段使わない/誤操作が怖い項目を
                        # コワーカー向けに隠せるように)。
                        prefs = menu_prefs.load_prefs()
                        menu = tk.Menu(self.root, tearoff=0, font=("Meiryo UI", 9))
                        menu.add_command(
                            label="⚙️ 編集",
                            command=lambda sk=side_key: self.open_settings_window(initial_side=sk),
                        )
                        if prefs.get("remember_position", True):
                            remember_var = tk.BooleanVar(
                                value=self.window_state.get("remember_on_exit", False)
                            )
                            menu.add_checkbutton(
                                label="📌 終了時の配置を記憶する（自由配置中の側のみ）",
                                variable=remember_var,
                                command=lambda v=remember_var: self._toggle_remember_position(v.get()),
                            )
                        menu.add_separator()
                        if prefs.get("close_this_side", True):
                            menu.add_command(
                                label="⚙️ このパレットだけを閉じる",
                                command=lambda h=target_hwnd, sk=side_key: self.close_one_side(h, sk),
                            )
                        if prefs.get("show_hidden", True):
                            menu.add_command(
                                label="👁️ 隠したパレットを再表示",
                                command=lambda h=target_hwnd: self.show_hidden_palettes(h),
                            )
                        if prefs.get("reset_preset", True):
                            menu.add_command(
                                label="🔄 初期構成を選び直す",
                                command=self._on_reset_to_preset,
                            )
                        if prefs.get("exit", True):
                            menu.add_command(
                                label="❌ JwNaviシステムを終了する",
                                command=self.shutdown_manager,
                            )
                        menu.post(event.x_root, event.y_root)

                    toolbar_l.bind("<Button-3>", lambda e: show_exit_popup(e, side_key="左"))
                    toolbar_r.bind("<Button-3>", lambda e: show_exit_popup(e, side_key="右"))
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
                    is_reload = hwnd in self._pending_pin_restore
                    pending_pins = self._pending_pin_restore.pop(hwnd, {})
                    for side_key, tb in (("左", toolbar_l), ("右", toolbar_r)):
                        if side_key in pending_pins:
                            x, y = pending_pins[side_key]
                            tb.is_pinned = True
                            tb.pin_btn.configure(text="自由", bg="#e1e1e1", relief="raised")
                            tb.wm_geometry(f"+{x}+{y}")
                            tb.update_idletasks()
                            tb._last_geom = None
                        elif not is_reload:
                            # 👑 設定保存によるリロードでは、記憶位置の復元は
                            # 行わない（追従だった側は追従のまま）。これは
                            # アプリ起動時・jw_cad新規検出時だけの処理。
                            self._restore_pinned_position(tb, side_key)
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        if pid:
                            self._win_event_watch_pids[hwnd] = pid
                            self.win_event_watcher.watch_pid(pid)
                    except Exception as e:
                        self.write_system_log(f"⚠️ WinEvent監視登録失敗 [HWND:{hwnd}]: {str(e)}")
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
        # 👑 破棄すると新しいToolbarはis_pinned=Falseから始まってしまい、
        # 自由配置していたパレットが保存のたびに追従モードへ戻ってしまう
        # 不具合があった（ユーザー指摘）。破棄前に自由配置中だった側の
        # 位置を覚えておき、作り直した直後に再適用する。
        # 👑 【自由配置→保存で追従に戻るバグの逆パターン】以前は「自由配置
        # だった側の位置を覚えておく」pending_pinsを、1側でも自由配置が
        # あった時だけhwnd単位で作っていた。すると「両側とも追従中に設定を
        # 保存」した場合、pending_pinsにそのhwndのキー自体が無いため、
        # 後段の再ドッキング処理が「新規に検出したjw_cadウィンドウ」と
        # 区別できず、window_state.json（終了時に記憶した自由配置位置）を
        # 誤って復元し、追従だったはずが自由配置に化けていた（ユーザー
        # 指摘、2026-08-31）。両側とも追従でも必ずhwnd自体のキーは作り、
        # 「これは設定保存によるリロードであって新規検出ではない」ことを
        # 後段が判別できるようにする。
        pending_pins = {}
        for hwnd in list(self.active_launchers.keys()):
            pair = self.active_launchers.pop(hwnd, None) or {}
            pins = {}
            for side_key, tb in pair.items():
                if tb.is_pinned:
                    pins[side_key] = (tb.winfo_x(), tb.winfo_y())
                try:
                    tb.destroy()
                except Exception:
                    pass
            pending_pins[hwnd] = pins
            self.event_engines.pop(hwnd, None)
            self.locked_intent.pop(hwnd, None)
        self._pending_pin_restore = pending_pins
        self.root.after(50, self._rebuild_palettes_now)

    def _rebuild_palettes_now(self):
        try:
            self._manage_palette_lifecycle(self.find_all_jw_cad_windows())
        except Exception as e:
            self.write_system_log(f"❌ パレット再構築失敗: {str(e)}")

    def open_settings_window(self, initial_side="左"):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            self.settings_window.select_tab(initial_side)
            return
        self.settings_window = SettingsWindow(self.root, manager_ref=self, initial_side=initial_side)

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

    def _update_checked_highlight(self, hwnd, tl, tr, current_state, matched_rule, click_confirmed):
        # 👑 【CHECKEDビット方式】jw_cad自身のツールバーのTBSTATE_CHECKED
        # ビットを直接読み、その場でパレットの凹み表示に反映する。
        # ステータスバー文言の解析やAMBIGUOUS_GROUPS等の衝突解決は不要
        # （jw_cad自身が最初から正確に区別している）。
        # 👑 ただし「ソリッド」等、今表示中でないツールバーページにボタンが
        # あるコマンドはTB_GETSTATEで判定不能（None）になる（実測で発覚）。
        # その場合だけ旧ステータスバー方式（JP_MATCH_MAP）にフォールバック
        # する。
        try:
            sides = (("左", tl), ("右", tr))
            locked_name = self._get_active_locked_intent(hwnd)
            matched_side, matched_btn = None, None
            if locked_name:
                # 👑 送信直後の一瞬、jw_cad側のCHECKED反映がまだ間に合って
                # いない場合があるため、ロック中はそちらを優先する。
                # 👑 【重大】ボタン名の文字列一致だけで探すため、線属性
                # ボタン(kind=auto_attr)にユーザーが本物のコマンドと同じ
                # 名前(例:「寸法」)を付けると衝突する(実機で発覚:
                # 「線属性の寸法はへこまずに、元の寸法コマンドがへこんで
                # いる」)。command_keyを持たない(=実コマンドに対応しない)
                # ボタンは、名前が一致してもここでの対象から除外する。
                for side_key, tb in sides:
                    for btn in tb.buttons:
                        if not btn.command_key:
                            continue
                        if btn.name == locked_name or (locked_name == "面取" and btn.name == "面取り"):
                            matched_side, matched_btn = side_key, btn
                            break
                    if matched_btn:
                        break
            else:
                id_map = {}
                for side_key, tb in sides:
                    for btn in tb.buttons:
                        id_cmd = command_master.get_id_command(btn.command_key)
                        if id_cmd:
                            id_map[id_cmd] = (side_key, btn)
                if id_map:
                    checked_states = get_command_checked_states(hwnd, id_map.keys())
                    checked_id = next((i for i, v in checked_states.items() if v is True), None)
                    if checked_id is not None:
                        matched_side, matched_btn = id_map[checked_id]
                    else:
                        undetermined_ids = {i for i, v in checked_states.items() if v is None}
                        if undetermined_ids and (
                            is_hover_trustworthy_rule(matched_rule)
                            or (click_confirmed and matched_rule.endswith("_TOOLTIP"))
                        ):
                            reverse_btn_name = current_state.replace("STATE_", "")
                            match_keyword = JP_MATCH_MAP.get(reverse_btn_name, None)
                            if match_keyword:
                                for idc in undetermined_ids:
                                    side_key, btn = id_map[idc]
                                    if btn.name == match_keyword or (
                                        match_keyword == "面取" and btn.name == "面取り"
                                    ):
                                        matched_side, matched_btn = side_key, btn
                                        break

            # 👑 「それは解除できないんだっけ？」への対応。線属性ボタン
            # (補助線等)が有効な間は、対応する本物のコマンドボタン側の
            # 凹み表示は出さず、トリガー側の凹みだけで表す(二重凹みの
            # 解除)。トリガー自身のハイライトはstart_auto_attr_sequence/
            # _revert_auto_attrが別途独立管理しているので、ここでは本物側を
            # 単に「マッチなし」扱いにするだけでよい。
            pending = self._auto_attr_pending.get(hwnd)
            if pending and matched_btn is not None and matched_btn.command_key == pending.get("target_command"):
                matched_btn = None
                matched_side = None

            for side_key, tb in sides:
                if tb.current_selected_button and tb.current_selected_button is not matched_btn:
                    tb.current_selected_button.clear_selected()
                    tb.current_selected_button = None

            if matched_btn:
                target_tb = tl if matched_side == "左" else tr
                if target_tb.current_selected_button is not matched_btn:
                    self.write_system_log(
                        f"[ボタン反映/CHECKED] 選択ボタン={matched_btn.name} side={matched_side}"
                    )
                    target_tb.select_button(matched_btn)
        except Exception as e:
            self.write_system_log(f"❌ CHECKEDハイライト更新エラー [HWND:{hwnd}]: {str(e)}")

    # ===== ✂️ main.py END PART 2 ✂️ =====
    # ===== ✂️ main.py START PART 3 ✂️ =====
    def _execute_pipeline_tick(self, hwnd, t_loop_start, click_confirmed=False):
        tl = self.active_launchers[hwnd]["左"]
        tr = self.active_launchers[hwnd]["右"]
        self._check_auto_attr_revert(hwnd)
        if tl.user_hidden and tr.user_hidden:
            return

        if win32gui.IsIconic(hwnd):
            if tl.winfo_viewable():
                tl.withdraw()
            if tr.winfo_viewable():
                tr.withdraw()
            return
        else:
            # 👑 「このパレットだけを閉じる」で片側だけuser_hidden=Trueに
            # なっている場合は、そちら側だけ再表示しないようにする
            # （以前は左右どちらか片方が実質「hwnd全体を隠すフラグ」を
            # 兼ねていて、閉じたつもりが両方消えるバグになっていた）。
            if not tl.winfo_viewable() and len(tl.buttons) > 0 and not tl.user_hidden:
                tl.deiconify()
            if not tr.winfo_viewable() and len(tr.buttons) > 0 and not tr.user_hidden:
                tr.deiconify()

        self._update_button_enabled_states(hwnd, tl, tr)

        raw_text = get_raw_statusbar_text(hwnd)
        # 👑 【2.0仕様：ステータスバーテキストのクリーンアップ強化】
        # コマンド名に続く「（例：線）」のような注釈だけを削除する。
        # 以前は「(」以降を丸ごと削る広すぎる正規表現になっており、
        # 「線・円マウス(L)部分消し」のような、括弧が文言の本体に含まれる
        # WAIT文言（消去・ハッチ・AUTO・距離点・図形登録等）まで巻き込んで
        # 破壊し、それらのコマンドが永久にWAIT状態を検知できなくなっていた
        # （実測で発覚）。「例」という文字を含む括弧だけに絞る。
        clean_raw_text = re.sub(r"[\s　]*[\(（]\s*例\s*[:：][^）\)]*[\)）]\s*$", "", raw_text).strip()

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

        # 👑 【CHECKEDビット方式・experiment/checked-bit-highlight】
        # 旧方式（ステータスバー文言をstate_parser.pyで解析し、JP_MATCH_MAPで
        # ボタン名へ変換）は、jw_cadが同じ文言を複数コマンドで使い回すため
        # AMBIGUOUS_GROUPS/INFERRED_WAIT等の複雑な衝突解決が必要だった。
        # jw_cad自身のツールバーボタンはTB_GETSTATEのTBSTATE_CHECKEDビットで
        # 「今アクティブなコマンドはどれか」を最初から正確に区別して持って
        # いることが実測で判明したため（線=CHECKED中に矩形=CHECKEDでない、
        # を確認）、これを直接読む方式に切り替えた。旧方式のコード
        # （state_parser.py・JP_MATCH_MAP・is_hover_trustworthy_rule等）は
        # ツールバーボタンを持たないコマンドへのフォールバックとして温存
        # してあるが、現状この経路からは呼んでいない。
        self._update_checked_highlight(hwnd, tl, tr, current_state, matched_rule, click_confirmed)

    def logged_execute_command(self, hwnd, command_id):
        # 👑 補助線モード中(直線=AUTO_ATTR_TARGET_COMMANDが既にCHECKED済み)に
        # 素の「線」ボタンを改めて押した場合、CHECKEDビットは「同じC001の
        # まま」なので_check_auto_attr_revertのTick監視では変化を検知でき
        # ない(ユーザー報告: 「補助線ぬけて直線の時はコマンドが変わって
        # ない認定」「線種も戻らない」)。この直接クリックをここでフックし、
        # 「補助線モードを抜けて戻る」合図として扱う。confirmedがまだ
        # Falseの間(=start_auto_attr_sequence自身が直後に送る初回の
        # 切替そのもの)は誤爆させない。
        pending = self._auto_attr_pending.get(hwnd)
        if pending and pending.get("confirmed") and command_id == pending.get("target_command"):
            self._revert_auto_attr(hwnd)

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

    MACRO_STEP_DELAY_MS = 300

    def execute_macro_sequence(self, hwnd, command_ids, index=0):
        # 👑 マクロ(グループボタン)の連続実行。time.sleep()でブロッキング
        # せず、root.after()で次のステップを予約することでUIを固まらせ
        # ない。各ステップはlogged_execute_command()をそのまま呼ぶので、
        # 有効/無効チェック・ログ・選択ハイライトは単発実行と同じく効く。
        # ステップ間隔はjw_cad側の反応速度を見て実機調整する想定の値。
        if index >= len(command_ids):
            return
        self.logged_execute_command(hwnd, command_ids[index])
        self.root.after(
            self.MACRO_STEP_DELAY_MS,
            lambda: self.execute_macro_sequence(hwnd, command_ids, index + 1),
        )

    # 👑 「電灯配線図」のようなレイヤ状態の保存/復元ボタン(kind=
    # "layer_snapshot")。ボタン専用のJWLファイル(config/layer_snapshots/
    # <snapshot_id>.jwl)が無ければ保存フロー、あれば復元フローへ分岐する。
    # 詳細はdoc/シート管理_設計メモ.md、doc/HANDOFF_layer_control.md参照。
    def handle_layer_snapshot_click(self, hwnd, entry, trigger_btn=None, side_type=None):
        # 👑 保存/復元は別ボタン(entry["role"])に分かれている(右クリック=
        # 保存は直感的でないというユーザー判断、2026-09-04)。
        # 👑 trigger_btnはtoolbar.py側で押した瞬間にset_selected()済み
        # (「押した瞬間に時間がかかる旨を表示したい」への対応、既存の
        # 凹み表示を流用)。この関数の全ての出口でclear_selected()を
        # 呼び戻す必要がある(即座に終わる分岐も含む)。
        if entry.get("role") == palette_config.LAYER_SNAPSHOT_ROLE_SAVE:
            self._start_layer_snapshot_save(hwnd, trigger_btn, side_type)
            return
        dest_path = palette_config.layer_snapshot_path(entry.get("snapshot_id", ""))
        if os.path.isfile(dest_path):
            self._restore_layer_snapshot(hwnd, dest_path, entry, trigger_btn)
        else:
            self.write_system_log(f"❌ [レイヤ復元] {entry.get('name')} はまだ保存されていません(対応する保存ボタンを先に押してください)")
            if trigger_btn:
                trigger_btn.clear_selected()

    def _start_layer_snapshot_save(self, hwnd, trigger_btn, side_type):
        # 👑 2026-09-04設計: 保存ボタンは汎用の1個のみで、押すたびに名前を
        # 聞く(「保存の度に名前を付けたい」)。既存の復元ボタンに同名の
        # ものがあれば上書き確認、無ければ新しい復元ボタンをこの保存
        # ボタンのすぐ後ろに自動で追加する(「保存ボタンは1個で復元
        # ボタンをたくさん」)。
        if hwnd in self._pending_layer_saves:
            self.write_system_log("[レイヤ保存] 既に保存待機中です")
            if trigger_btn:
                trigger_btn.clear_selected()
            return

        dlg = TextInputDialog(
            self.root, title="レイヤ情報を保存", label="名前:", initial="",
            note="保存には10秒程度かかります",
        )
        self.root.wait_window(dlg)
        name = dlg.result
        if not name:
            if trigger_btn:
                trigger_btn.clear_selected()
            return

        config = palette_config.load_config()
        existing_id = None
        for side in palette_config.SIDES:
            for group in palette_config.side_config(config, side)["groups"]:
                for btn in group.get("buttons") or []:
                    if (
                        btn.get("kind") == palette_config.BUTTON_KIND_LAYER_SNAPSHOT
                        and btn.get("role") == palette_config.LAYER_SNAPSHOT_ROLE_RESTORE
                        and btn.get("snapshot_name") == name
                    ):
                        existing_id = btn.get("snapshot_id")
                        break
                if existing_id:
                    break
            if existing_id:
                break

        if existing_id:
            if not messagebox.askyesno(
                "レイヤ情報を保存", f"「{name}」は既に保存されています。上書きしますか?", parent=self.root,
            ):
                if trigger_btn:
                    trigger_btn.clear_selected()
                return
            snapshot_id = existing_id
        else:
            snapshot_id = uuid.uuid4().hex
            save_name = (trigger_btn.entry.get("name") if trigger_btn and trigger_btn.entry else None) or "ﾚｲﾔ\n保存"
            target_side, gi, insert_at = self._find_layer_save_insert_position(config, side_type, save_name)
            restore_btn = palette_config.new_layer_snapshot_button(
                name, palette_config.LAYER_SNAPSHOT_ROLE_RESTORE,
                snapshot_id=snapshot_id, snapshot_name=name,
            )
            palette_config.side_config(config, target_side)["groups"][gi]["buttons"].insert(insert_at, restore_btn)
            palette_config.save_config(config)
            self._refresh_all_toolbar_buttons()

        dest_path = palette_config.layer_snapshot_path(snapshot_id)
        self.write_system_log(f"[レイヤ保存] {name} を保存中です(7〜10秒程度かかります)…")

        def worker():
            pending = layer_snapshot.trigger_save(hwnd)
            self.root.after(0, lambda: self._on_layer_save_triggered(hwnd, dest_path, {"name": name}, pending, trigger_btn))

        threading.Thread(target=worker, daemon=True).start()

    def _find_layer_save_insert_position(self, config, preferred_side, save_name):
        # 👑 新しい復元ボタンは、押された保存ボタンのすぐ後ろに挿入する
        # (ユーザー決定: 「置き場所は保存ボタンのすぐ後ろが自然」)。
        # 同名の保存ボタンが複数ある場合はpreferred_side側を優先する。
        sides_order = [preferred_side] + [s for s in palette_config.SIDES if s != preferred_side] if preferred_side else list(palette_config.SIDES)
        for side in sides_order:
            groups = palette_config.side_config(config, side)["groups"]
            for gi, group in enumerate(groups):
                buttons = group.get("buttons") or []
                for bi, btn in enumerate(buttons):
                    if (
                        btn.get("kind") == palette_config.BUTTON_KIND_LAYER_SNAPSHOT
                        and btn.get("role") == palette_config.LAYER_SNAPSHOT_ROLE_SAVE
                        and btn.get("name") == save_name
                    ):
                        return side, gi, bi + 1
        # 見つからなければ、優先サイドの末尾グループの末尾へ
        side = preferred_side or palette_config.SIDES[0]
        groups = palette_config.side_config(config, side)["groups"]
        if not groups:
            groups.append(palette_config.new_group())
        return side, len(groups) - 1, len(groups[-1]["buttons"])

    def _refresh_all_toolbar_buttons(self):
        # 👑 新しい復元ボタンの追加はconfig.json全体(両面)に影響するため、
        # 開いている全てのjw_cadウィンドウのパレットを更新する。
        for hwnd in list(self.active_launchers.keys()):
            self._refresh_toolbar_buttons(hwnd)

    def _on_layer_save_triggered(self, hwnd, dest_path, entry, pending, trigger_btn):
        if not pending:
            self.write_system_log(f"❌ [レイヤ保存] jw_cadの実行フォルダが特定できず開始できませんでした name={entry.get('name')}")
            if trigger_btn:
                trigger_btn.clear_selected()
            return
        self._pending_layer_saves[hwnd] = {
            "pending": pending, "dest_path": dest_path, "started_at": time.time(), "name": entry.get("name"),
            "trigger_btn": trigger_btn,
        }
        # 👑 monitor_loop()の1秒周期だけに頼ると検知が最大1秒近く遅れる
        # ため、保存待ちの間だけ短い周期(0.3秒)で追加ポーリングする
        # (ユーザー要望:「保存もう少し早くならないかな」)。
        self.root.after(300, self._check_pending_layer_saves)

    def _restore_layer_snapshot(self, hwnd, jwl_path, entry, trigger_btn):
        # 👑 保存側と同じ理由でtrigger_restore()も別スレッドで実行する。

        def worker():
            ok = layer_snapshot.trigger_restore(hwnd, jwl_path)
            self.root.after(0, lambda: self._on_layer_restore_done(entry, ok, trigger_btn))

        threading.Thread(target=worker, daemon=True).start()

    def _on_layer_restore_done(self, entry, ok, trigger_btn):
        if ok:
            self.write_system_log(f"[レイヤ復元] {entry.get('name')} を適用しました")
        else:
            self.write_system_log(f"❌ [レイヤ復元] {entry.get('name')} の適用に失敗しました(ダイアログが見つかりませんでした)")
        if trigger_btn:
            trigger_btn.clear_selected()

    def _check_pending_layer_saves(self):
        # 👑 monitor_loop()(1秒周期)に加え、保存待ちの間は_start_layer_
        # snapshot_save()から0.3秒周期でも自発的に呼ばれる(下の再スケジュール
        # 部分参照)。完了(LAYER_RESTORE.JWLの更新)をここで監視する。
        if not self._pending_layer_saves:
            return
        # 👑 編集可能なレイヤが無い等で外部変形が完了しない場合、以前は
        # 120秒待たないとボタンが凹んだまま(=押せない)戻らなかった
        # (ユーザー報告:「保存おしたら、レイヤ情報を保存が押せなくなった」)。
        # 正常な保存は7〜10秒程度で終わるため、余裕を見て20秒で見切る。
        LAYER_SAVE_TIMEOUT_SEC = 20
        now = time.time()
        for hwnd in list(self._pending_layer_saves.keys()):
            state = self._pending_layer_saves[hwnd]
            trigger_btn = state.get("trigger_btn")
            if now - state["started_at"] > LAYER_SAVE_TIMEOUT_SEC:
                self.write_system_log(
                    f"❌ [レイヤ保存] {state['name']} がタイムアウトしました"
                    f"(編集可能なレイヤが無い等で、選択する図形が無かった可能性があります)"
                )
                if trigger_btn:
                    trigger_btn.clear_selected()
                del self._pending_layer_saves[hwnd]
                continue
            if layer_snapshot.check_save_complete(state["pending"]):
                try:
                    layer_snapshot.finalize_save(state["pending"], state["dest_path"])
                    self.write_system_log(f"[レイヤ保存] {state['name']} を保存しました")
                    # 👑 _refresh_toolbar_buttons()はNavButtonを作り直す
                    # ため、古いtrigger_btnへのclear_selected()は不要
                    # (新しいボタンは最初から非選択状態で生成される)。
                    self._refresh_toolbar_buttons(hwnd)
                except Exception as exc:
                    self.write_system_log(f"❌ [レイヤ保存] {state['name']} の保存に失敗しました: {exc}")
                    if trigger_btn:
                        trigger_btn.clear_selected()
                del self._pending_layer_saves[hwnd]
        if self._pending_layer_saves and not self._shutdown_requested:
            self.root.after(300, self._check_pending_layer_saves)

    def _refresh_toolbar_buttons(self, hwnd):
        # 👑 _manage_palette_lifecycle()はhwndの出現/消滅しか見ておらず、
        # 既存ツールバーの再描画はしないため、レイヤ保存ボタンの「保存済」
        # 表示切替のように「configは変わったがhwnd自体は変わっていない」
        # ケースでは明示的にload_and_build_buttons()を呼ぶ必要がある。
        launcher = self.active_launchers.get(hwnd)
        if not launcher:
            return
        for side in ("左", "右"):
            toolbar = launcher.get(side)
            if toolbar:
                try:
                    toolbar.load_and_build_buttons()
                except Exception as exc:
                    self.write_system_log(f"❌ ツールバー再描画失敗: {exc}")

    # 👑 「補助線」「配線」等(kind="auto_attr")。押した瞬間の線属性を覚えて
    # 指定の線属性へ切替→切替先コマンドへ移動、その後hwndごとに監視して
    # 他コマンドへ切り替わったら自動で元の線属性へ戻す。詳細はdoc/
    # 補助線ボタン_要件書.md参照。_auto_attr_pendingは__init__で初期化。
    # 切替先コマンドはボタンごとに設定可能(既定は直線=C001、ユーザー要望:
    # 「他のコマンド選択することできる？連続線とか」)。
    AUTO_ATTR_DEFAULT_TARGET_COMMAND = "C001"  # 直線

    def start_auto_attr_sequence(self, hwnd, entry, trigger_btn=None):
        # 👑 既にこのhwndで補助線系モードが有効な状態でもう一度押した場合
        # (同じボタンの連打、または別の補助線系ボタンへの切替)、今の
        # jw_cad側の線属性は既に補助線系プリセットに変わってしまっている
        # ため、ここで読み直すと本来の「元の線属性」を上書きして失って
        # しまう(ユーザー報告: 「もう一度押すと逃がした線種情報が消える」)。
        # 既にpendingがあれば、その"original"を引き継ぐ。
        existing = self._auto_attr_pending.get(hwnd)
        # 👑 「補助線2回目押したときに水平垂直のチェック外すのお願いする
        # の忘れてた」→「そこは直線と同じ挙動にしたい」。jw_cadは同じ
        # 描画ツールを再選択すると水平・垂直チェックを自分で外す(実機
        # 確認済み、_check_auto_attr_revert付近の既存コメント参照)。
        # 初回押下時だけJwNavigator側で明示的にONへ再アサートし、同じ
        # 補助線ボタンの2回目以降の押下ではその上書きをせず、直線を
        # 再選択した時と同じ(jw_cad任せの)挙動に任せる。
        same_button_repress = bool(existing and existing.get("trigger_btn") is trigger_btn)
        if existing:
            original = existing["original"]
            old_trigger = existing.get("trigger_btn")
            if old_trigger and old_trigger is not trigger_btn:
                try:
                    old_trigger.clear_selected()
                except Exception:
                    pass
        else:
            original = line_attr_dialog.read_current_attr(hwnd)
            if original is None:
                self.write_system_log("❌ [補助線系ボタン] 線属性の読み取りに失敗しました。")
                return
            orig_group, orig_layer = line_attr_dialog.read_current_layer_group(hwnd)
            original["group"] = orig_group
            original["layer"] = orig_layer
        ok = line_attr_dialog.apply_attr(
            hwnd, entry.get("line_color"), entry.get("line_type"), entry.get("line_width") or None
        )
        if not ok:
            self.write_system_log("❌ [補助線系ボタン] 線属性の変更に失敗しました。")
            return
        target_group = entry.get("layer_group")
        target_layer = entry.get("layer_number")
        if target_group is not None or target_layer is not None:
            if not line_attr_dialog.set_layer_group(hwnd, target_group, target_layer):
                self.write_system_log("⚠️ [補助線系ボタン] レイヤ切替に失敗しました(線属性は変更済み)。")
        target_command = entry.get("target_command") or self.AUTO_ATTR_DEFAULT_TARGET_COMMAND
        self._auto_attr_pending[hwnd] = {
            "original": original, "confirmed": False, "trigger_btn": trigger_btn,
            "horizontal_vertical": bool(entry.get("horizontal_vertical")),
            "target_command": target_command,
        }
        auto_attr_state.save_pending(self._auto_attr_pending)
        if trigger_btn:
            # 👑 「凹むの遅い」という指摘のため、tickでのCHECKEDビット監視を
            # 待たず即座に凹ませる。この凹み表示は独立管理(トリガー自身の
            # command_keyは変更しない)なので、本物の「線」ボタンの表示には
            # 一切影響しない。
            trigger_btn.set_selected()
        self.logged_execute_command(hwnd, target_command)
        if entry.get("horizontal_vertical") and not same_button_repress:
            # 👑 「水平･垂直」は直線コマンドの条件設定バー上のコントロール
            # で、切替直後は反映がまだ間に合っていないことがあるため、
            # 少し待ってからクリックする(実機調整の値)。ただし同じ補助線
            # ボタンの2回目以降の押下では強制ONし直さない(「そこは直線と
            # 同じ挙動にしたい」＝jw_cad自身が同じツール再選択時に外す
            # 動きへ任せる)。
            self.root.after(200, lambda: line_attr_dialog.set_horizontal_vertical(hwnd, True))

    def _check_auto_attr_revert(self, hwnd):
        pending = self._auto_attr_pending.get(hwnd)
        if not pending:
            return
        line_id = command_master.get_id_command(pending["target_command"])
        checked = get_command_checked_states(hwnd, [line_id]).get(line_id)
        if checked is True:
            # 👑 直線への切替がjw_cad側に反映されたことを確認できるまでは
            # 「まだ切り替わっていないだけ」の可能性があるので戻し判定に
            # 入らない(切替直後の1tick目でFalse/Noneを誤って「離脱した」と
            # 判定してしまう競合を避けるため)。
            if not pending["confirmed"]:
                pending["confirmed"] = True
                auto_attr_state.save_pending(self._auto_attr_pending)
            # 👑 「補助線から抜ける時、jw_cad本体の直線ボタンでは抜けられ
            # ないのか」への対応。C001は既にCHECKEDのままなので上のFalse
            # 判定では検知できないが、jw_cad自身のツールバーを物理的に
            # クリックした瞬間だけTBSTATE_PRESSEDが立つ(JwNavigator経由の
            # 送信では立たない)ので、それを「抜ける合図」として拾う。
            # logged_execute_command側のフック(JwNavigatorパレット経由の
            # 「線」クリック用)と対になる、jw_cad本体側クリック用の経路。
            pressed = get_command_pressed_states(hwnd, [line_id]).get(line_id)
            if pressed is True:
                self._revert_auto_attr(hwnd)
            return
        if checked is False and pending["confirmed"]:
            self._revert_auto_attr(hwnd)

    def _revert_auto_attr(self, hwnd):
        pending = self._auto_attr_pending.pop(hwnd, None)
        if not pending:
            return
        auto_attr_state.save_pending(self._auto_attr_pending)
        trigger_btn = pending.get("trigger_btn")
        if trigger_btn:
            try:
                trigger_btn.clear_selected()
                # 👑 箱(フライアウト)の中身として補助線系ボタンが選ばれて
                # いた場合、command_keyを使わない独自ハイライト管理のため
                # clear_selected()内蔵の箱復帰ロジックでは拾えない。
                # 明示的に箱自身の顔へ戻す(単体の補助線ボタンならkindが
                # auto_attrなので中で何もしない)。
                trigger_btn.revert_group_face()
            except Exception:
                pass
        original = pending["original"]
        line_attr_dialog.apply_attr(hwnd, original["color"], original["type"], original["width"] or None)
        orig_group = original.get("group")
        orig_layer = original.get("layer")
        if orig_group is not None or orig_layer is not None:
            line_attr_dialog.set_layer_group(hwnd, orig_group, orig_layer)
        if pending.get("horizontal_vertical"):
            # 👑 「補助線と直線は別コマンドとして扱いたいので、直線を押して
            # 抜けた際に水平垂直が外れるのを回避してほしい」への対応。
            # jw_cad自身が「線」を再選択した時に条件設定バーの水平･垂直
            # チェックを内部的にリセットしてしまう挙動が実機で見られた
            # ため、少し待ってから改めてONを再アサートし直す(まだ直線
            # コマンドのままなのでコントロール自体は引き続き存在する。
            # 別コマンドへ離脱した場合はコントロールが見つからずFalseに
            # なるだけで無害)。
            self.root.after(200, lambda: line_attr_dialog.set_horizontal_vertical(hwnd, True))
        self.write_system_log("↩️ [補助線系ボタン] 線属性・レイヤを元に戻しました。")

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

    def _toggle_remember_position(self, enabled):
        # 👑 トグル自体は即座にディスクへ保存する（正常終了しなかった場合でも
        # 設定自体は次回起動時に残るように）。実際の座標保存はshutdown_manager
        # 側で行う。
        self.window_state["remember_on_exit"] = bool(enabled)
        try:
            window_state.save_state(self.window_state)
        except Exception as e:
            self.write_system_log(f"⚠️ 設定保存エラー: {str(e)}")

    def _restore_pinned_position(self, tb, side_key):
        # 👑 「終了時の配置を記憶する」設定がONの時だけ、自由配置（ピン留め）
        # だった側の位置を復元する。保存位置が画面外（モニター構成が変わった
        # 等）だと二度と手の届かない場所に固定される事故になるため、必ず
        # 画面内かを検証してから復元し、ダメなら通常の追従モードのまま
        # 何もしない（ユーザーからの明示的な懸念指摘を受けての安全策）。
        if not self.window_state.get("remember_on_exit"):
            return
        pos = self.window_state.get(side_key)
        if not pos or len(tb.buttons) == 0:
            return
        try:
            w = tb.winfo_reqwidth()
            h = tb.winfo_reqheight()
            virtual_screen = (
                win32api.GetSystemMetrics(76),
                win32api.GetSystemMetrics(77),
                win32api.GetSystemMetrics(78),
                win32api.GetSystemMetrics(79),
            )
            if not window_state.is_on_screen(pos["x"], pos["y"], w, h, virtual_screen):
                self.write_system_log(
                    f"⚠️ {side_key}パレットの保存位置が画面外のため復元をスキップしました。"
                )
                return
            tb.is_pinned = True
            tb.pin_btn.configure(text="自由", bg="#e1e1e1", relief="raised")
            tb.wm_geometry(f"+{pos['x']}+{pos['y']}")
            # 👑 wm_geometry()だけだと、イベントループが回るまで実際の移動が
            # 反映されないことがある（sync_toolbar_positionの通常同期でも
            # 同じ理由でupdate_idletasks()している）。ここで呼び忘れていた
            # ため、保存位置を正しく計算していても画面(0,0)に見えたまま
            # だった（実測で確認、2026-08-27）。
            tb.update_idletasks()
            tb._last_geom = None
        except Exception as e:
            self.write_system_log(f"⚠️ {side_key}パレット位置復元エラー: {str(e)}")

    def close_one_side(self, hwnd, side_key):
        # 👑 以前はここでtl/tr両方をdestroy()していて、「このパレットだけを
        # 閉じる」つもりが両方閉じてしまうバグだった（ユーザー指摘）。
        # destroy()すると二度と復元できないため、withdraw()（非表示化）+
        # user_hidden=Trueに変更し、show_hidden_palettes()でいつでも
        # 再表示できるようにする。
        if hwnd not in self.active_launchers:
            return
        tb = self.active_launchers[hwnd][side_key]
        tb.user_hidden = True
        tb.withdraw()

    def show_hidden_palettes(self, hwnd):
        if hwnd not in self.active_launchers:
            return
        for side_key in ("左", "右"):
            tb = self.active_launchers[hwnd][side_key]
            if tb.user_hidden:
                tb.user_hidden = False
                if len(tb.buttons) > 0:
                    tb.deiconify()

    def shutdown_manager(self):
        if self._shutdown_requested:
            return
        self._shutdown_requested = True
        if self.tray_icon:
            self.tray_icon.destroy()
            self.tray_icon = None
        if self.mouse_hook_controller:
            self.mouse_hook_controller.stop()
        if self.keyboard_hook_controller:
            self.keyboard_hook_controller.stop()
        if self.win_event_watcher:
            self.win_event_watcher.stop()

        if self.window_state.get("remember_on_exit"):
            try:
                for hwnd in list(self.active_launchers.keys()):
                    tl = self.active_launchers[hwnd]["左"]
                    tr = self.active_launchers[hwnd]["右"]
                    self.window_state["左"] = (
                        {"x": tl.winfo_x(), "y": tl.winfo_y()} if tl.is_pinned else None
                    )
                    self.window_state["右"] = (
                        {"x": tr.winfo_x(), "y": tr.winfo_y()} if tr.is_pinned else None
                    )
                window_state.save_state(self.window_state)
            except Exception as e:
                self.write_system_log(f"⚠️ パレット位置保存エラー: {str(e)}")

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
        # 👑 SetWinEventHook（アクセシビリティ通知）は上記の低レベル入力フックとは
        # 別のAPIで、対象プロセスへのコード注入を伴わないため別途有効化している。
        # jw_cadのステータスバー更新を即座に検知し、1秒周期のポーリングでは
        # 取りこぼしがちな短命な文言（矩形の1点目等）を補う。
        self.win_event_watcher.start()
        self._monitor_job = self.root.after(500, self.monitor_loop)
        self.root.after(500, self._fast_sync_loop)
        self.root.after(30, self._drain_hook_queue)
        self.root.after(30, self._drain_win_event_queue)
        self._create_tray_icon()
        self.root.mainloop()

    def _create_tray_icon(self):
        try:
            self.tray_icon = TrayIcon(
                tooltip="JwNavigator",
                menu_items_provider=self._tray_menu_items,
                on_default_click=self.open_settings_window,
            )
        except Exception as e:
            self.write_system_log(f"⚠️ タスクトレイアイコン作成に失敗しました: {str(e)}")

    def _tray_menu_items(self):
        # 👑 状態収集ログ(詳細ログ)のトグルはここに置かず、別途独立した
        # ログ収集システムとして作る方針にしたため外してある
        # （ユーザー方針：「ログをとってほしい時だけ起動する」別ツール）。
        # 👑 トレイメニューは、右クリックメニュー側のON/OFF設定(menu_prefs)
        # の影響を受けず、常にフルセットを表示する(ユーザー要望:
        # 「タスクトレイのほうには右クリックメニュー全部載せといてね」
        # ＝コワーカー向けに右クリックを簡略化しても、開発者/管理側は
        # トレイから常に全機能へアクセスできるようにする)。「この◯
        # パレットだけを閉じる」だけは対象のhwnd/sideを一意に選べない
        # ため、トレイには載せない。
        remember_on = self.window_state.get("remember_on_exit", False)
        return [
            ("⚙️ 編集", self.open_settings_window, None),
            ("📌 終了時の配置を記憶する", lambda: self._toggle_remember_position(not remember_on), remember_on),
            ("👁️ 隠したパレットを再表示", self._show_all_hidden_palettes, None),
            ("🔄 初期構成を選び直す", self._on_reset_to_preset, None),
            ("", None, None),
            ("❌ JwNaviシステムを終了する", self.shutdown_manager, None),
        ]

    def _show_all_hidden_palettes(self):
        for hwnd in list(self.active_launchers.keys()):
            self.show_hidden_palettes(hwnd)

    def _on_reset_to_preset(self):
        # 👑 「初期設定ミスったな」と思った時のやり直し導線。config.jsonを
        # 手動削除しないと出せなかった初回起動の選択画面を、いつでも
        # 呼び出せるようにする(ユーザー要望、配布直前に追加)。
        if not messagebox.askyesno(
            "確認",
            "今のパレット構成を、選び直した初期構成で上書きします。\n"
            "(今のボタン配置は失われます。保存は不要です・押した瞬間に上書きされます)\n"
            "続けますか?",
            parent=self.root,
        ):
            return
        if run_preset_reset(self.root):
            self.reload_all_palettes()
            self.write_system_log("🔄 初期構成を選び直しました。")

    def _drain_win_event_queue(self):
        # 👑 SetWinEventHookのコールバック（別スレッド）が積んだイベントを、
        # ここ（Tkinterメインスレッド）でまとめて処理する。1回のドレインで
        # 同じhwndに複数イベントが積まれていても、_execute_pipeline_tickは
        # hwndごとに1回だけ呼ぶ（setで重複排除）。
        hwnds_to_refresh = set()
        while True:
            try:
                hwnd = self.win_event_watcher.event_queue.get_nowait()
            except queue.Empty:
                break
            try:
                root_hwnd = win32gui.GetAncestor(hwnd, 2)  # GA_ROOT
            except Exception:
                continue
            if root_hwnd in self.active_launchers:
                hwnds_to_refresh.add(root_hwnd)

        for hwnd in hwnds_to_refresh:
            try:
                self._execute_pipeline_tick(hwnd, time.perf_counter())
            except Exception as e:
                self.write_system_log(f"❌ WinEvent即時更新エラー [HWND:{hwnd}]: {str(e)}")

        if not self._shutdown_requested:
            self.root.after(30, self._drain_win_event_queue)


if __name__ == "__main__":
    manager = JwNavigatorManager()
    # 👑 Ctrl+C(SIGINT)や、taskkill /F無しでの終了要求でも、正規終了パス
    # (shutdown_manager)を通してパレット位置をちゃんと保存できるように
    # する。フックしないと強制終了扱いになり、window_state.jsonが更新
    # されないまま残り続けてしまう(実機で繰り返し確認した不具合)。
    signal.signal(signal.SIGINT, lambda signum, frame: manager.shutdown_manager())
    signal.signal(signal.SIGTERM, lambda signum, frame: manager.shutdown_manager())
    manager.start()
# ===== ✂️ main.py END PART 3 ✂️ =====
