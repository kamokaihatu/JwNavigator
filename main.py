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
from utils.send_command import send_command_to_hwnd, is_command_enabled, get_command_states, get_command_checked_states, get_command_pressed_states, describe_toolbars
from utils import line_attr_dialog
from utils import command_master
from utils.jww_watcher import get_raw_statusbar_text
from utils.state_parser import parse_statusbar_text
from utils.state_patterns import is_hover_trustworthy_rule
from utils.state_collection import StateCollectionLogger
from utils.win_event_watcher import WinEventWatcher
from utils.palette_layout import compute_palette_geometry
from utils import window_state
from utils import external_transform_setup
from utils import diagnostics
from controllers.layer_save import LayerSaveMixin
from controllers.auto_attr import AutoAttrMixin
from utils import app_paths
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


# 👑 2026-09-16: レイヤ保存とモードボタンはcontrollers/配下へ切り出した。
# メソッドを移しただけで動作は変えていない(各ファイルの冒頭コメント参照)。
class JwNavigatorManager(LayerSaveMixin, AutoAttrMixin):
    def __init__(self):
        self.root = tk.Tk()
        # 👑 2026-09-14: kosakaの高DPI環境(Windowsの拡大率100%超)で発覚した
        # 不具合の修正。SetProcessDpiAwareness(2)導入後、tkinterはウィンドウ
        # のあるモニタの実DPIを見てフォント(create_text等のfont=正の整数
        # =ポイント指定)を自動で拡大するようになった。一方、このアプリの
        # パレットボタンのキャンバス寸法(button_size設定値)や設定画面の
        # .geometry("800x680")等は生のピクセル値の決め打ちで、DPIに応じて
        # 拡大されない。結果、DPI100%超の環境だけ「文字がボタンからはみ
        # 出す」「設定画面の保存/キャンセルボタンが枠外に押し出される」
        # という不具合が起きていた(kamoの開発機は100%のため再現しなかった)。
        # tk自身のポイント→ピクセル換算係数(tk scaling)を96DPI相当の値へ
        # 固定することで、フォントもこのアプリの既存のピクセル前提の
        # レイアウトと同じ基準に揃える(ネイティブなWindowsダイアログ・
        # ウィンドウ枠は影響を受けず、実DPIに応じて正しく拡大され続ける、
        # tk scalingはtkinter自身の描画にのみ効くため)。
        try:
            self.root.tk.call("tk", "scaling", 96 / 72)
        except Exception:
            pass
        self.root.withdraw()

        # 👑 【リスト直撃クラッシュ完全埋葬】 sys.argvの0番目（文字列）を正確に参照してPath型エラーを防止
        script_path_str = sys.argv[0] if sys.argv else ""
        exe_dir = (
            os.path.dirname(os.path.abspath(script_path_str))
            if script_path_str
            else os.getcwd()
        )
        self.log_file_path = os.path.join(exe_dir, "JwNavigator_Log.txt")
        # 👑 2026-09-16: ログは開きっぱなしにする。1行ごとにopen/closeして
        # いた頃は実測で**1行あたり約12.5ミリ秒**かかっていた(法人向け
        # ウイルス対策ソフトがファイルを開くたびに走査しているためと思われ
        # る)。監視ループが毎秒2行出すので、それだけで毎秒25ミリ秒を
        # メインスレッドで浪費していた計算になる。ハンドルを保持すると
        # 20マイクロ秒/行(約620倍)まで落ちた。os.path.getsizeも毎回
        # 呼んでいたが、実測では誤差だったのでtell()に置き換えた。
        self._log_fp = None
        # 👑 2026-09-16: 「探したが見つからなかった」を黙って握りつぶさない
        # ための共通記録先(utils/diagnostics.py)。ここでログ出力先を渡す。
        diagnostics.set_log_sink(self.write_system_log)
        self.write_system_log("--- JwNavigator Ver3.76 メインシステム始動 ---")

        # 👑 2026-09-11: 「exeを入れ替え/移動しても設定が消えないように」、
        # パッケージ版は設定の保存先を%APPDATA%\JwNavigator\へ移した
        # (DECISIONS.md参照)。この下のrun_first_launch_setup_if_needed()
        # や_auto_attr_pending読み込みが「新しい場所」を見に行く前に、
        # 以前のexe隣接config\から一度だけ引き継いでおく必要がある
        # (でないと既存ユーザーが「設定が消えた」「初回起動画面が
        # また出た」と誤認する)。log_file_pathは直前で設定済みなので
        # write_system_logはこの時点でも使える。
        app_paths.migrate_legacy_config_if_needed(log=self.write_system_log)

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
        self._save_notice_window = None
        self.settings_window = None
        self.last_jww_state = "STATE_IDLE"
        self.locked_intent = (
            {}
        )  # 👑 コマンド実行中の凹み上書き防止ロック（インテントホールド、値は(name, timestamp)）
        self.mouse_hook_controller = MouseHookController(self)
        self.keyboard_hook_controller = KeyboardHookController(self)
        self.win_event_watcher = WinEventWatcher()
        self._win_event_watch_pids = {}  # hwnd -> pid（unwatch時に使う）
        # 👑 フックコールバックはここへイベントを積むだけ。実処理はメインスレッドのdrainで行う。
        self.hook_event_queue = queue.Queue()

        # 👑 exe_dir/self.log_file_pathは__init__の先頭(migrate_legacy_
        # config_if_needed()より前)で既に計算済み、ここではそれを流用する。
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
        self.prevent_overlap = True
        self.palette_edges = {}
        self.palette_positions = {}
        self._gcom100_checked = False
        # 👑 2026-09-16: 環境スナップショット(約30行)は1セッション1回だけ。
        # Jw_win.jwfが無い環境では_gcom100_checkedを意図的に立て直さない
        # ため、この歯止めが無いとjw_cadを検出するたびに毎回吐いてしまう。
        self._env_described = False
        self._gcom_conflict_notified = False
        self._missing_jw_win_notified = False
        self.window_state = window_state.load_state()
        self._pending_pin_restore = {}
        self.tray_icon = None
        self.root.withdraw()
        external_transform_setup.ensure_deployed(log=self.write_system_log)

    LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB

    def write_system_log(self, text):
        # 👑 flushは毎回行う(__init__のコメント参照)。バッファに溜めると
        # 速くはなるが、クラッシュや強制終了の直前の数行が消える。トレイ
        # アイコンのクラッシュ調査(Ver3.71)では、まさにその末尾数行が
        # 決め手だったため、速度より確実性を優先する。flushを入れても
        # 20マイクロ秒/行で、open/close方式の620分の1で済む。
        now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            f = self._log_fp
            if f is None or f.closed:
                f = self._log_fp = open(self.log_file_path, "a", encoding="utf-8")
            f.write(f"[{now_str}] {text}\n")
            f.flush()
            if f.tell() > self.LOG_MAX_BYTES:
                self._rotate_log()
        except Exception as e:
            print(f"Log Write Error: {e}")

    def _rotate_log(self):
        # 👑 配布後は開発時と違って無制限に増え続けても誰も気づかないため、
        # 一定サイズを超えたら古い前半を切り捨てる簡易ローテーション。
        # 不具合報告時にログをコピペしてもらう運用は残したいので、
        # 完全に消さず直近分は必ず残す。
        # 👑 2026-09-16: ハンドルを保持する方式にしたため、書き換える前に
        # 必ず閉じる(次の書き込みで開き直される)。
        try:
            if self._log_fp is not None:
                self._log_fp.close()
        except Exception:
            pass
        self._log_fp = None
        try:
            with open(self.log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            keep = lines[len(lines) // 2:]
            with open(self.log_file_path, "w", encoding="utf-8") as f:
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
    def _get_exe_path_for_hwnd(hwnd):
        handle = None
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            handle = win32api.OpenProcess(
                win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid
            )
            return win32process.GetModuleFileNameEx(handle, 0)
        except Exception:
            return None
        finally:
            if handle:
                win32api.CloseHandle(handle)

    @staticmethod
    def _get_exe_name_for_hwnd(hwnd):
        path = JwNavigatorManager._get_exe_path_for_hwnd(hwnd)
        return os.path.basename(path).lower() if path else None

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
        toolbars = self.active_launchers[hwnd]
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
                    # 👑 自由(ピン留め)中のパレットは、追従中の他パレットの
                    # 重なり防止スタッキングから除外する(ユーザー要望、
                    # 2026-09-10)。utils/palette_layout.pyのcompute_palette_
                    # geometry参照。
                    "is_pinned": tb.is_pinned,
                }
            # 👑 N枚パレット対応(2026-09-10): tl/tr決め打ちをやめ、
            # active_launchers[hwnd]の中身(可変長)をそのままループする形に
            # 変更した。compute_palette_geometry()自体は2026-09-09に
            # sides辞書を受け取る形へ既に一般化済み。
            sides = {key: _side_info(tb) for key, tb in toolbars.items()}
            geom = compute_palette_geometry(
                jw_rect, screen_width, virtual_screen, sides,
                edges=self.palette_edges, positions=self.palette_positions,
                prevent_overlap=self.prevent_overlap,
            )

            for key, tb in toolbars.items():
                if not geom.get(key):
                    continue
                w, h, x, y = geom[key]
                if tb.is_pinned:
                    # 👑 「自由モード中にもボタンが増えたら伸ばしてほしい」
                    # (ユーザー要望、2026-09-10)。自由(ピン留め)配置は
                    # 位置だけユーザーの手元に任せ、サイズ(w,h)は通常通り
                    # ボタン数から再計算した値に追従させる。x,yは現在の
                    # 実際の位置をそのまま使い、動かさない。
                    x, y = tb.winfo_x(), tb.winfo_y()
                new_geom = (w, h, x, y)
                # 位置が変わっていないのに毎回wm_geometry()を呼ぶと、
                # Windows側で「位置が更新された」扱いになり、意図せず
                # 最前面に上がってくることがある（実測で確認）。実際に
                # 変化があった時だけ呼ぶ。
                if getattr(tb, "_last_geom", None) != new_geom:
                    tb.wm_geometry(f"{w}x{h}+{x}+{y}")
                    # wm_geometry()だけだと、他の操作（ボタン押下など）で
                    # イベントループが回るまで実際の描画に反映されないことが
                    # あるため、ここで強制的に反映させる。
                    tb.update_idletasks()
                    tb._last_geom = new_geom
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

            palette_real_ids = {_real_top_level_hwnd(tb) for tb in toolbars.values()}
            for side_label, tb in toolbars.items():
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
                for tb in self.active_launchers[hwnd].values():
                    if tb:
                        tb.destroy()
                del self.active_launchers[hwnd]
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
                    toolbars = {}
                    config = palette_config.load_config()
                    self.prevent_overlap = bool(config.get("prevent_overlap", True))
                    self.palette_edges = dict(config.get("edges") or {})
                    self.palette_positions = dict(config.get("positions") or {})
                    side_keys = palette_config.all_side_keys(config)
                    for side_key in side_keys:
                        toolbars[side_key] = Toolbar(
                            master=self.root,
                            side_type=side_key,
                            hwnd=hwnd,
                            execute_func=self.logged_execute_command,
                            manager_ref=self,
                        )
                    # 👑 待機中ラベルは先頭(左)側にのみ付ける
                    # (main.py内の他の箇所からtl.status_labelという
                    # 前提で参照されており、両側に付けると混乱するため)。
                    # 👑 2026-09-16: "左"は削除できるようになったので、
                    # 固定で参照せず「今あるパレットの先頭」を使う。
                    first_key = side_keys[0]
                    toolbars[first_key].status_label = tk.Label(
                        toolbars[first_key],
                        text="待機中",
                        font=("Meiryo UI", 7),
                        bg="#f0f0f0",
                        fg="#888888",
                    )
                    toolbars[first_key].status_label.pack(side="top", fill="x", pady=(0, 2))

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

                    for side_key, tb in toolbars.items():
                        tb.bind("<Button-3>", lambda e, sk=side_key: show_exit_popup(e, side_key=sk))
                        tb.deiconify()

                    self.active_launchers[hwnd] = toolbars
                    self.root.update_idletasks()
                    for tb in toolbars.values():
                        tb.update_idletasks()
                    is_reload = hwnd in self._pending_pin_restore
                    pending_pins = self._pending_pin_restore.pop(hwnd, {})
                    for side_key, tb in toolbars.items():
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
                    # 👑 「レイヤ情報保存」用のGCOM_100(Ctrl+J)キー割り付けを
                    # jw_cad側のプロファイルに自動登録する(2026-09-11、
                    # DECISIONS.md参照)。アプリ起動中1回だけでよいので
                    # フラグで抑制する。jw_cadのexeフォルダはhwndから辿る。
                    if not self._gcom100_checked:
                        self._gcom100_checked = True
                        try:
                            jw_exe_path = self._get_exe_path_for_hwnd(hwnd)
                            if jw_exe_path:
                                reserved = self._jw_cad_reserved_ctrl_letters(hwnd)
                                result = external_transform_setup.ensure_gcom100_registered(
                                    os.path.dirname(jw_exe_path),
                                    log=self.write_system_log,
                                    reserved_letters=reserved,
                                )
                                # 👑 2026-09-16: 既定のCtrl+J/Ctrl+Kが他の外部
                                # 変形に使われていた場合、登録側は空いている
                                # スロットへ回す。実際に送るキーもそこへ
                                # 合わせないと意味がないので反映する
                                # (utils/layer_snapshot.pyの
                                # set_external_transform_keys参照)。
                                layer_snapshot.set_external_transform_keys(
                                    result.get("save_key_letter"),
                                    result.get("fast_save_key_letter"),
                                )
                                if result["new_registration"]:
                                    self._notify_jw_cad_restart_required()
                                if result["conflicts"] and not self._gcom_conflict_notified:
                                    self._gcom_conflict_notified = True
                                    self._notify_gcom_conflict(result["conflicts"])
                                if (
                                    not result["has_jw_win"]
                                    and not self._missing_jw_win_notified
                                    and self._has_layer_save_button()
                                ):
                                    self._missing_jw_win_notified = True
                                    self._notify_missing_jw_win_jwf(
                                        os.path.dirname(jw_exe_path)
                                    )
                                # 👑 2026-09-16: 登録の「結果」を必ず残す。他人の
                                # PCは頻繁に触れないため、1回のログで原因が
                                # 確定できるようにしておく(kosakaPCの調査参照)。
                                if not self._env_described:
                                    self._env_described = True
                                    external_transform_setup.describe_environment(
                                        os.path.dirname(jw_exe_path), log=self.write_system_log
                                    )
                                    self._log_display_and_toolbar_environment(hwnd)
                                # 👑 2026-09-16: Jw_win.jwfが無い環境では、登録
                                # しても永久に効かない(GCOMはこのファイルから
                                # しか読まれない)。利用者が案内に従って後から
                                # 作った場合に拾えるよう、確認済みフラグを立て
                                # 直さず、次にjw_cadを検出した時にもう一度確認
                                # する。案内どおりjw_cadを再起動すればそのまま
                                # 登録が走る(kosakaPCの手順で「JwNavigatorも
                                # 再起動が要る」という余計な条件を無くすため)。
                                if not external_transform_setup.has_jw_win_jwf(
                                    os.path.dirname(jw_exe_path)
                                ):
                                    self._gcom100_checked = False
                            else:
                                # 👑 ここが無言で素通りすると「GCOM_100が古い展開先の
                                # ままで、原因がログから追えない」事故になる
                                # (実機発覚、2026-09-11)。原因不明でも痕跡だけは残す。
                                self.write_system_log(
                                    "⚠️ GCOM_100自動登録確認: jw_cad.exeのパスが取得できず"
                                    "スキップしました。"
                                )
                        except Exception as e:
                            self.write_system_log(f"⚠️ GCOM_100自動登録確認に失敗しました: {str(e)}")
                except Exception as e:
                    self.write_system_log(
                        f"❌ パレット動的構築失敗 [HWND:{hwnd}]: {str(e)}"
                    )

    # 👑 jw_cadのメニューに出てこないが、利用者が当然使えると思っている
    # Windows定番のキー。奪うと「Ctrl+Aが効かなくなった」と言われるので
    # 外部変形の割り当て先からは常に除外する。
    _ALWAYS_RESERVED_CTRL_LETTERS = frozenset("AF")

    def _jw_cad_reserved_ctrl_letters(self, hwnd):
        """jw_cad自身がCtrl+英字で使っているキーを、メニューのアクセラレータ
        表示から読み取って返す(実測: 新規作成=Ctrl+N、上書き保存=Ctrl+S、
        コピー=Ctrl+C 等)。外部変形の割り当て先を自動で決める際、ここに
        入っているキーは避ける。
        👑 推測した固定リストではなく実機から読むのは、jw_cadのバージョンや
        利用者のカスタマイズで変わり得るため(2026-09-16、kamoの指摘
        「Ctrl+Aとかターゲットが違ったら違う話になります」への対応)。"""
        letters = set(self._ALWAYS_RESERVED_CTRL_LETTERS)
        user32 = ctypes.windll.user32

        def walk(menu, depth):
            try:
                count = win32gui.GetMenuItemCount(menu)
            except Exception:
                return
            for i in range(count):
                try:
                    buf = ctypes.create_unicode_buffer(256)
                    user32.GetMenuStringW(menu, i, buf, 256, win32con.MF_BYPOSITION)
                    text = buf.value
                    sub = user32.GetSubMenu(menu, i)
                except Exception:
                    continue
                if sub and depth < 3:
                    walk(sub, depth + 1)
                elif "\t" in text:
                    accel = text.split("\t", 1)[1].strip().upper()
                    if accel.startswith("CTRL+") and len(accel) == len("CTRL+") + 1:
                        letters.add(accel[-1])

        try:
            walk(win32gui.GetMenu(hwnd), 0)
        except Exception:
            pass
        return letters

    def _log_display_and_toolbar_environment(self, hwnd):
        # 👑 2026-09-16: 他人のPCは頻繁に触れないため、1回の起動ログで環境差を
        # 追えるようにする。DPIはkosakaPCで「文字がボタンからはみ出す」不具合の
        # 原因だった要素(DECISIONS.md 2026-09-14参照)。ツールバー構成は
        # 補助線モードのCHECKED判定がNoneになるかどうかを左右する
        # (utils/send_command.pyのdescribe_toolbars()参照)。
        try:
            dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
        except Exception:
            dpi = None
        try:
            sw = ctypes.windll.user32.GetSystemMetrics(0)
            sh = ctypes.windll.user32.GetSystemMetrics(1)
        except Exception:
            sw = sh = None
        self.write_system_log(
            f"🔎 [環境] 画面={sw}x{sh} DPI={dpi}"
            f"(96で等倍、{'拡大表示あり' if dpi and dpi != 96 else '拡大なし'})"
        )
        try:
            count, button_counts = describe_toolbars(hwnd)
            self.write_system_log(
                f"🔎 [環境] jw_cadのツールバー数={count} 各ボタン数={button_counts}"
            )
        except Exception as e:
            self.write_system_log(f"🔎 [環境] ツールバー情報の取得に失敗: {e}")
        try:
            reserved = sorted(self._jw_cad_reserved_ctrl_letters(hwnd))
            self.write_system_log(
                f"🔎 [環境] 外部変形に使わないCtrl+英字(jw_cadが使用中+定番): {''.join(reserved)}"
            )
        except Exception as e:
            self.write_system_log(f"🔎 [環境] Ctrl+英字の使用状況の取得に失敗: {e}")
        try:
            # 👑 レイヤ/レイヤグループのバーをどう見分けたか(名前で判別
            # できたか、位置推定に落ちたか)。落ちていると両者が入れ替わる
            # 可能性があるため、環境ごとに必ず残す。
            line_attr_dialog._find_layer_group_buttons(hwnd)
            self.write_system_log(
                f"🔎 [環境] レイヤ/レイヤグループのバー判別: "
                f"{line_attr_dialog.describe_layer_bar_detection()}"
            )
        except Exception as e:
            self.write_system_log(f"🔎 [環境] レイヤバー判別の確認に失敗: {e}")
        # 👑 2026-09-16: 起動時点で既に記録されている「見つからなかった」を
        # まとめて出す(set_log_sink前のnote()はログに出ないため、ここで拾う)。
        for key, message in diagnostics.describe().items():
            self.write_system_log(f"🔎 [環境] {key}: {message}")

    _MESSAGE_LOCK = threading.Lock()

    def _show_message_async(self, text, icon=0x40):
        """👑 2026-09-16: MessageBoxWをメインスレッドから呼ぶと、OKを押すまで
        Tkのイベントループごと止まる。これらの案内はjw_cadを検出した直後
        (=パレットを生成している最中)に出るため、実機では「起動したら
        パレットが画面の隅に張り付いたまま固まり、警告が出ている」状態に
        なっていた(検証中に実際に踏んだ)。ワーカースレッドから出せば
        パレットの生成は止まらない(MessageBoxWは自前のメッセージループを
        持つので、hwnd=0ならワーカースレッドから呼んで問題ない)。
        複数の案内が同時に出て重ならないよう、ロックで順番に出す。"""
        def worker():
            with self._MESSAGE_LOCK:
                try:
                    ctypes.windll.user32.MessageBoxW(0, text, "JwNavigator", icon)
                except Exception:
                    pass

        try:
            threading.Thread(target=worker, daemon=True).start()
        except Exception:
            pass

    def _has_layer_save_button(self):
        # 👑 Jw_win.jwfが無いことを画面で知らせるのは、レイヤ保存を実際に
        # 使う人だけにする(使わない人には無関係な警告になるため)。
        try:
            config = palette_config.load_config()
        except Exception:
            return False
        for side in config.get("sides", {}).values():
            for group in side.get("groups", []):
                for btn in group.get("buttons", []):
                    if (
                        btn.get("kind") == palette_config.BUTTON_KIND_LAYER_SNAPSHOT
                        and btn.get("role") == palette_config.LAYER_SNAPSHOT_ROLE_SAVE
                    ):
                        return True
        return False

    def _notify_missing_jw_win_jwf(self, jw_cad_exe_dir):
        # 👑 2026-09-16: jw_cadはGCOM(外部変形のキー割り付け)をレジストリに
        # 保存せず、起動時にJw_win.jwfからしか読まない。このファイルは
        # jw_cad側で一度も「環境設定ファイルの書込み」をしたことがないPCには
        # 存在せず、その場合レイヤ保存は**何度再起動しても永久に動かない**。
        # kosakaPCがこの状態で、ログを読むまで原因が誰にも分からなかった。
        # ログだけでは気づけないので、レイヤ保存ボタンを持っている人には
        # 画面で伝える(_has_layer_save_button参照)。
        self.write_system_log(
            "⚠️ Jw_win.jwfが無いため、レイヤ保存が使えない状態です(画面で案内しました)。"
        )
        self._show_message_async(
            "レイヤ保存を使うための準備が1つ残っています。\n\n"
            f"jw_cadのフォルダ({jw_cad_exe_dir})に Jw_win.jwf がありません。\n"
            "jw_cadは外部変形のキー割り付けをこのファイルからしか読まないため、\n"
            "このままではレイヤ保存は動作しません。\n\n"
            "【対処方法】\n"
            "1. jw_cadで [設定] → [環境設定ファイル] → [書込み] を選ぶ\n"
            f"2. {jw_cad_exe_dir} に「Jw_win.jwf」という名前で保存する\n"
            "3. jw_cadを再起動する\n\n"
            "現在の設定がそのまま保存されるだけなので、設定は変わりません。\n"
            "一度行えば、以後はこの案内は出ません。",
            icon=0x30,  # MB_ICONWARNING
        )

    def _notify_gcom_conflict(self, conflicts):
        # 👑 2026-09-16: Ctrl+J/Ctrl+Kを既に自分の外部変形で使っている人の
        # プロファイルは、他人の登録を壊さないため意図的に書き換えない。
        # ただしその場合レイヤ保存は永久に使えず、今まではログを読まないと
        # 気づけなかった。黙って使えないのが一番たちが悪いので知らせる。
        detail = "\n".join(
            f"・{name} の {key_label} は「{current}」が使用中"
            for name, key_label, current in conflicts
        )
        self._show_message_async(
            "レイヤ保存に使う外部変形を、jw_cadへ登録できませんでした。\n"
            "空いているキーが見つからなかったためです。\n"
            "他の設定を壊さないよう、既に使われている割り当ては書き換えません。\n\n"
            f"{detail}\n\n"
            "このままではレイヤ保存は使えません。\n"
            "jw_cadの[設定]→[環境設定ファイル]で、上記のどれか1つの割り当てを\n"
            "外してからJwNavigatorを再起動してください。",
            icon=0x30,  # MB_ICONWARNING
        )

    def _notify_jw_cad_restart_required(self):
        # 👑 2026-09-16: jw_cadはキー割り付け(GCOM_1XX)を自分の起動時にしか
        # 読み込まない。既にjw_cadが起動している状態で初回登録を行った場合、
        # ファイルには書けても起動中のjw_cadには反映されず、Ctrl+J/Ctrl+Kを
        # 送っても完全に無反応になる(kosakaPCの実機ログで発覚。新規登録の
        # 直後にレイヤ保存(全自動)を実行したところ、jw_cad側の状態が一切
        # 変化しないまま「選択確定」ボタンのタイムアウトで失敗していた)。
        # 症状がログ無しでは原因不明の「保存できない」にしか見えないため、
        # 登録した時点で利用者へはっきり案内する。
        self.write_system_log(
            "⚠️ レイヤ保存用のキー割り付けを新規登録しました。"
            "jw_cadは起動時にしか割り付けを読まないため、"
            "一度jw_cadを閉じて開き直すまでレイヤ保存は動作しません。"
        )
        self._show_message_async(
            "レイヤ保存用のキー割り付けをjw_cadへ登録しました。\n\n"
            "jw_cadは起動時にしかキー割り付けを読み込まないため、\n"
            "お手数ですが一度jw_cadを閉じて開き直してください。\n"
            "(この案内が出るのは初回だけです)"
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

    def _update_button_enabled_states(self, hwnd, toolbars):
        # jw_cad実ツールバーの有効/無効状態をまとめて調べ、対応するパレット
        # ボタンをグレーアウト/クリック無効化する。無効と判定できたものだけ
        # 反映し、判定不能（そのコマンドが今のツールバーに出ていない等）
        # なものは今まで通りクリック可能なままにする。
        try:
            id_map = {}
            for tb in toolbars.values():
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

    def _update_checked_highlight(self, hwnd, toolbars, current_state, matched_rule, click_confirmed):
        # 👑 【CHECKEDビット方式】jw_cad自身のツールバーのTBSTATE_CHECKED
        # ビットを直接読み、その場でパレットの凹み表示に反映する。
        # ステータスバー文言の解析やAMBIGUOUS_GROUPS等の衝突解決は不要
        # （jw_cad自身が最初から正確に区別している）。
        # 👑 ただし「ソリッド」等、今表示中でないツールバーページにボタンが
        # あるコマンドはTB_GETSTATEで判定不能（None）になる（実測で発覚）。
        # その場合だけ旧ステータスバー方式（JP_MATCH_MAP）にフォールバック
        # する。
        try:
            sides = tuple(toolbars.items())
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
                target_tb = toolbars[matched_side]
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
        toolbars = self.active_launchers[hwnd]
        self._check_auto_attr_revert(hwnd)
        if all(tb.user_hidden for tb in toolbars.values()):
            return

        if win32gui.IsIconic(hwnd):
            for tb in toolbars.values():
                if tb.winfo_viewable():
                    tb.withdraw()
            return
        else:
            # 👑 「このパレットだけを閉じる」で片側だけuser_hidden=Trueに
            # なっている場合は、そちら側だけ再表示しないようにする
            # （以前は左右どちらか片方が実質「hwnd全体を隠すフラグ」を
            # 兼ねていて、閉じたつもりが両方消えるバグになっていた）。
            for tb in toolbars.values():
                if not tb.winfo_viewable() and len(tb.buttons) > 0 and not tb.user_hidden:
                    tb.deiconify()

        self._update_button_enabled_states(hwnd, toolbars)

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

        status_tb = next(
            (tb for tb in toolbars.values() if hasattr(tb, "status_label")), None
        )
        if status_tb is not None and hasattr(status_tb, "status_label"):
            if current_state == "STATE_IDLE":
                status_tb.status_label.configure(text="待機中", fg="#888888")

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
        self._update_checked_highlight(hwnd, toolbars, current_state, matched_rule, click_confirmed)

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
        for tb in self.active_launchers.get(hwnd, {}).values():
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
        for tb in self.active_launchers[hwnd].values():
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
                    for side_key, tb in self.active_launchers[hwnd].items():
                        self.window_state[side_key] = (
                            {"x": tb.winfo_x(), "y": tb.winfo_y()} if tb.is_pinned else None
                        )
                window_state.save_state(self.window_state)
            except Exception as e:
                self.write_system_log(f"⚠️ パレット位置保存エラー: {str(e)}")

        for hwnd in list(self.active_launchers.keys()):
            for tb in self.active_launchers[hwnd].values():
                if tb:
                    tb.destroy()
        try:
            self.root.after_cancel(self._monitor_job)
        except Exception as exc:
            logging.exception("shutdown_manager after_cancel failed")
        # 👑 開きっぱなしにしているログのハンドルを閉じる(write_system_log
        # 参照)。毎回flushしているので閉じ忘れても内容は失われないが、
        # 終了後にログファイルを削除/移動できるようにしておく。
        try:
            if self._log_fp is not None:
                self._log_fp.close()
                self._log_fp = None
        except Exception:
            pass
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
        self.root.after(50, self._poll_tray_pending)
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

    def _poll_tray_pending(self):
        # 👑 2026-09-15: タスクトレイの生WNDPROC(ctypesコールバック)から
        # 直接呼ぶと不定タイミングでクラッシュする不具合が実機で見つかった
        # ため(utils/tray_icon.pyのコメント参照)、トレイ操作の実行は
        # ここ(既存のTkイベントループの`.after()`)からだけ行う。
        if self.tray_icon is not None:
            try:
                self.tray_icon.poll_pending()
            except Exception as e:
                self.write_system_log(f"⚠️ トレイ操作の処理エラー: {str(e)}")
        self.root.after(50, self._poll_tray_pending)

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
