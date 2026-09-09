# ===== ✂️ utils/layer_snapshot.py START ✂️ =====
"""
「電灯配線図」のようなレイヤ状態の保存/復元ボタン用の自動化。
doc/シート管理_設計メモ.md, doc/HANDOFF_layer_control.md参照。

保存: jw_cad側に外部変形(B_MARK.bat)をCtrl+<SAVE_KEY>のキー割り付け
(GCOM_100、config/keybind_setup.md参照)で登録しておき、そのキーを合成
送信するだけで起動する(外部変形自体のファイル選択ダイアログは独自の
owner-drawツリーで自動操作できないため、キー割り付け経由で迂回する)。

👑 2026-09-08変更: 以前は起動後に「全選択」→「選択確定」ボタンを自動
クリックしていた(=図面全体を選択するため、重い図面で15秒以上かかる、
doc/HANDOFF_layer_control.md 14章)。代わりに、`B_MARK.bat`が書込レイヤに
目印の点(1,1)を作図し、続けて`A_SAVE.bat`が範囲選択の始点/終点を
JwNavigator側からのキーボード直接タイプ(`0,0`→Enter→`2,2`→Shift+V)で
極小範囲(0,0)~(2,2)だけを対象にする。書込レイヤは定義上必ず編集可能
なので目印点は確実に選択でき、`#g1`は選択範囲の大小に関係なく256レイヤ
全部を返すため、この極小選択でも全レイヤ取得できる(実機確認済み)。
これにより「全選択」の実処理コスト(図面の重さに比例して増える)を
回避できる。

👑 2026-09-08既知の不具合: `B_MARK.bat`の返信に含めている`h/A_SAVE.BAT`
(仕様書527-530行目、外部変形の連鎖指定)には、**1回の操作(Ctrl+J1回)で
点作図→A_SAVE一式がまるごと2周してしまうことがある**という原因未特定の
不具合がある(連鎖なしで`A_SAVE`単体を直接キー起動した場合は1回しか
実行されないことを確認済みなので、連鎖の仕組み自体が原因と判定)。
代替として「`B_MARK`/`A_SAVE`を別ホットキーに分けてJwNavigator側で順番に
送る」方式も試したが、2つ目のホットキーがGCOM_1XXの想定通りには割り
付かず(jw_cadのキー割り付けの優先順位が仕様書の記述と食い違う可能性、
未解明)断念した。**2周する不具合は許容し、連鎖ありの現状の方式を
採用している**(たまに余分な点が作図され、保存が長くなることがある。
doc/HANDOFF_layer_control.md 21章参照)。

完了するとjw_cad実行フォルダ直下にLAYER_RESTORE.JWLが生成/更新
されるので、そのmtimeの変化を監視して完了を検知し、ボタン専用のファイル
にコピーする。

復元: 「設定→環境設定ファイル→読込み」(idCommand=32923)は標準の
Windows「開く」ダイアログを開くため、ファイル名欄への直接WM_SETTEXTと
「開く」ボタンのBM_CLICKだけで完全に無人実行できる(実機確認済み)。
"""
import ctypes
import os
import shutil
import time

import win32api
import win32con
import win32gui
import win32process

from utils import line_attr_dialog

VK_CONTROL = 0x11
SAVE_KEY_VK = 0x4A  # 'J' (Ctrl+J、GCOM_100の10番目=Jに割り付け済み)


class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def get_memory_status():
    """空きメモリの状況を返す(kamoの「空きメモリに左右されるのでは」
    という仮説の検証用、2026-09-09、psutil等の追加依存無しで
    GlobalMemoryStatusExを直接呼ぶ)。
    戻り値: (使用率%, 空き物理メモリMB, 全体物理メモリMB)、失敗時None。"""
    try:
        stat = _MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return None
        avail_mb = stat.ullAvailPhys / (1024 * 1024)
        total_mb = stat.ullTotalPhys / (1024 * 1024)
        return (stat.dwMemoryLoad, avail_mb, total_mb)
    except Exception:
        return None
LOAD_CONFIG_CMD_ID = 32923  # 設定→環境設定ファイル→読込み

# 👑 mark_point.pyのMARK_X/MARK_Yと必ず一致させること(2026-09-09)。
# 一度(100000,100000)まで離してみたが、遠い座標だとパン/再描画が
# 自動化の固定待ち時間に間に合わず、外部変形が「再選択」状態になって
# 手動操作が必要になる不具合が発生したため(1,1)に戻した。
MARK_X = 1
MARK_Y = 1

# 👑 B_MARKが書込レイヤに作図する目印点の後始末用(2026-09-09)。
# B_MARK.bat/A_SAVE.batが追記しているlayerdump\trace.txtの[MARK]行数を
# 保存の前後で比較し、実際に何回点が作図されたか(連鎖の2周バグがあれば
# 2回)を数えて、その回数だけ「戻る」を送って消す。GCOM_100/110の11番目
# のフォルダ指定と一致させること(現状の登録先はJWW_EXT)。
TRACE_LOG_PATH = r"C:\jww\JWW_EXT\layerdump\trace.txt"


def _count_marks():
    if not os.path.isfile(TRACE_LOG_PATH):
        return 0
    try:
        with open(TRACE_LOG_PATH, "r", encoding="cp932", errors="replace") as f:
            return sum(1 for line in f if line.startswith("[MARK]") and "enter" in line)
    except OSError:
        return 0


def force_foreground(hwnd):
    """SetForegroundWindow()は、呼び出し元スレッドが直前にユーザー入力を
    受けていない場合、Windowsのフォアグラウンドロックにより無言で失敗
    することがある(戻り値は見ていなかった)。定番の回避策として、現在
    フォアグラウンドのスレッドへ`AttachThreadInput`で入力キューを結合
    してから呼ぶ(2026-09-08、coworkの提案。保存に9秒前後かかる件の
    切り分けで、送信経路側の上乗せ分を減らせないか試験中)。"""
    try:
        fg_hwnd = win32gui.GetForegroundWindow()
        if fg_hwnd == hwnd:
            return True
        fg_thread, _ = win32process.GetWindowThreadProcessId(fg_hwnd)
        cur_thread = win32api.GetCurrentThreadId()
        attached = False
        try:
            if fg_thread and fg_thread != cur_thread:
                win32process.AttachThreadInput(cur_thread, fg_thread, True)
                attached = True
            return bool(win32gui.SetForegroundWindow(hwnd))
        finally:
            if attached:
                win32process.AttachThreadInput(cur_thread, fg_thread, False)
    except Exception:
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
        return False


def jw_cad_dir(hwnd):
    """指定hwndを持つjw_cadプロセスの実行フォルダ(LAYER_RESTORE.JWLの
    出力先)を返す。取得できなければNone。"""
    handle = None
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid
        )
        path = win32process.GetModuleFileNameEx(handle, 0)
        return os.path.dirname(path)
    except Exception:
        return None
    finally:
        if handle:
            win32api.CloseHandle(handle)


def restore_jwl_path(hwnd):
    d = jw_cad_dir(hwnd)
    if not d:
        return None
    return os.path.join(d, "LAYER_RESTORE.JWL")


VK_RETURN = 0x0D


def _send_vk(vk, shift=False):
    if shift:
        win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
    win32api.keybd_event(vk, 0, 0, 0)
    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
    if shift:
        win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.03)


def _type_text(text):
    # 👑 keybd_eventはハードウェアレベルの合成なので、WM_CHAR注入と違い
    # jw_cadの座標入力ハンドラでも実機で機能することを確認済み
    # (2026-09-08)。VkKeyScanでその時点のキーボード配列に合わせて
    # 文字→仮想キーコード+Shift要否を解決する(レイアウト非依存)。
    for ch in text:
        vk_shift = win32api.VkKeyScan(ch)
        vk = vk_shift & 0xFF
        shift = bool(vk_shift & 0x100)
        _send_vk(vk, shift=shift)


def _type_point(x, y, enter=True):
    _type_text("%g,%g" % (x, y))
    if enter:
        _send_vk(VK_RETURN)


def trigger_save(hwnd, log=None):
    """Ctrl+<SAVE_KEY>を送ってB_MARK.batを起動する。B_MARK.batは書込
    レイヤに目印の点(1,1)を作図してから`h/A_SAVE.BAT`でA_SAVE.batへ
    自動連鎖する。JwNavigator側は、A_SAVE.batの範囲選択(#h1)の始点・
    終点をキーボードで直接タイプする(`0,0`→Enter→`2,2`→Enter)。

    👑 2026-09-08変更の経緯: 以前は「全選択」ボタンを自動クリックして
    図面全体を選択していたが、重い図面で選択処理そのものに15秒以上
    かかることが判明した(doc/HANDOFF_layer_control.md 14章)。書込
    レイヤは定義上必ず編集可能、`#g1`は選択範囲の大小に関係なく256
    レイヤ全部を返す、という2つの性質を使い、目印点だけを囲む極小範囲を
    選択することで、全選択の実処理コストを回避する(実機確認済み:
    `jwc_temp.txt`が136KB→3.9KBに縮小、groups=16 layers=256は維持)。

    👑 タイミング注意(実機で1敗): Ctrl+J直後は範囲選択モードがまだ
    安定しておらず、早すぎるキー入力は座標として認識されずjw_cad全体の
    ショートカットキーとして誤動作する(線・ハッチ等の別コマンドが
    暴発した実例あり)。範囲選択モードが安定するまで待ってから送信する。

    👑 保存が7〜17秒かかる件のcowork調査用(2026-09-08)、各ステップの
    完了を`log`(呼び出し元のwrite_system_log等、文字列1個を受け取る
    callable)へ通知する。呼び出し側の既存ログが自動でタイムスタンプを
    付けるため、ここでは経過秒数を自前計算せず、イベント名だけ渡せば
    よい設計にしてある。
    戻り値: {"jwl_path":.., "baseline_mtime":..} (完了検知に使う)。
    jwl_pathが取得できなければNoneを返す。"""
    def _log(msg):
        if log:
            try:
                log(msg)
            except Exception:
                pass

    path = restore_jwl_path(hwnd)
    if not path:
        return None
    baseline = None
    if os.path.isfile(path):
        try:
            baseline = os.path.getmtime(path)
        except OSError:
            baseline = None
    mark_baseline = _count_marks()
    mem = get_memory_status()
    if mem:
        _log(f"[レイヤ保存詳細] 空きメモリ: {mem[1]:.0f}MB / {mem[2]:.0f}MB (使用率{mem[0]}%)")
    force_foreground(hwnd)
    time.sleep(0.2)
    if win32gui.GetForegroundWindow() != hwnd:
        # 👑 実機で事故発生(2026-09-08): 前面化に失敗したまま構わず
        # キー送信を続けたところ、Ctrl+J等が別アプリ(VSCode)に飛んで
        # しまった。keybd_eventはハードウェアレベルの合成でウィンドウを
        # 指定できないため、前面化が実際に成功したことを確認できない
        # 限り、以降のキー送信は絶対に行ってはならない。
        _log("❌[レイヤ保存詳細] jw_cadの前面化に失敗したため中断しました(誤ったウィンドウへの入力を防止)")
        return None
    _log("[レイヤ保存詳細] 前面化成功")

    # 👑 2026-09-08: 「B_MARK/A_SAVEを別ホットキーに分けてJwNavigator側で
    # 順番に送る」方式を試したが、2つ目のホットキー(Ctrl+K)がGCOM_1XXの
    # 想定通りには割り付かず(jw_cadのキー割り付け優先順位が未解明、
    # doc/HANDOFF_layer_control.md 21章参照)断念。連鎖(`h/A_SAVE.BAT`)には
    # 「1回の操作で一連の流れがまるごと2周することがある」既知の不具合
    # (原因未特定)が残るが、これは許容し、確実に動くこちらの方式を採用する。
    _log("[レイヤ保存詳細] Ctrl+J送信(点作図→A_SAVEへ連鎖)")
    win32api.keybd_event(VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(SAVE_KEY_VK, 0, 0, 0)
    win32api.keybd_event(SAVE_KEY_VK, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

    time.sleep(0.8)
    _log(f"[レイヤ保存詳細] 範囲始点({MARK_X},{MARK_Y})送信")
    _type_point(MARK_X, MARK_Y)
    time.sleep(0.3)
    _log(f"[レイヤ保存詳細] 範囲終点({MARK_X+2},{MARK_Y+2})送信(Enterなし)")
    _type_point(MARK_X + 2, MARK_Y + 2, enter=False)
    time.sleep(0.2)
    _log("[レイヤ保存詳細] Shift+Vで選択確定(以後はjw_cad内部処理待ち)")
    _send_vk(0x56, shift=True)  # V

    return {"jwl_path": path, "baseline_mtime": baseline, "mark_baseline": mark_baseline}


def cleanup_mark_points(hwnd, pending, log=None):
    """保存完了後に呼ぶ。trace.txtの[MARK]行数がtrigger_save()呼び出し時
    より増えた分(=連鎖の2周バグで余分に作図された分も含め、実際に作図
    された点の総数)だけ「戻る」(idCommand 57643)を送って消す。
    書込レイヤへの点作図以降、保存完了までの間に他の作図操作が挟まって
    いないという前提が必要(通常のボタン操作フローでは保証される)。"""
    def _log(msg):
        if log:
            try:
                log(msg)
            except Exception:
                pass

    if not pending:
        return
    baseline = pending.get("mark_baseline", 0)
    extra = _count_marks() - baseline
    if extra <= 0:
        return
    _log(f"[レイヤ保存詳細] 目印点を{extra}個作図した形跡を検知、Escapeで後始末します")
    # 👑 idCommand=57643へのWM_COMMAND、Ctrl+Zのキー合成、どちらも実機で
    # 効かなかった(2026-09-09)。kamoの手動テストで「マウスで戻るボタンを
    # クリック」だけでなく「キーボードでEscapeを2回」でも消えることが
    # 判明したため、より単純なEscapeキー合成に切り替える。前面化を確認
    # できない場合は送らない(force_foreground()と同じ安全原則)。
    for _ in range(extra):
        if win32gui.GetForegroundWindow() != hwnd:
            force_foreground(hwnd)
            time.sleep(0.2)
            if win32gui.GetForegroundWindow() != hwnd:
                _log("❌[レイヤ保存詳細] 前面化できずEscapeを中断しました")
                return
        win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
        win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.3)


def check_save_complete(pending):
    """trigger_save()の戻り値を渡す。ユーザーが範囲選択→確定を終えて
    LAYER_RESTORE.JWLが更新されたらTrue。"""
    if not pending:
        return False
    path = pending.get("jwl_path")
    if not path or not os.path.isfile(path):
        return False
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return False
    baseline = pending.get("baseline_mtime")
    if baseline is None:
        return True
    return mtime > baseline


def finalize_save(pending, dest_path):
    """完了を確認した後、LAYER_RESTORE.JWLをボタン専用の保存先へコピーする。"""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copyfile(pending["jwl_path"], dest_path)


def _find_new_window(cls, before_hwnds, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        found = []

        def cb(h, _extra):
            try:
                if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == cls:
                    found.append(h)
            except Exception:
                pass
            return True

        try:
            win32gui.EnumWindows(cb, None)
        except Exception:
            pass
        new_ones = [h for h in found if h not in before_hwnds]
        if new_ones:
            return new_ones[-1]
        time.sleep(0.1)
    return None


def _find_children(hwnd, cls):
    found = []

    def cb(h, _extra):
        try:
            if win32gui.GetClassName(h) == cls:
                found.append(h)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumChildWindows(hwnd, cb, None)
    except Exception:
        pass
    return found


def trigger_restore(hwnd, jwl_path, keep_write_layer=True, log=None):
    """「設定→環境設定ファイル→読込み」を自動実行し、jwl_pathを読み込ませる。
    実機確認済み(標準の「開く」コモンダイアログのため自動操作可能)。

    👑 JWLは書込レイヤグループ/レイヤを保存時点の値へ強制的に動かして
    しまう(`100`指定を省くと逆にファイル全体が無視されると実機で判明、
    2026-09-04)。keep_write_layer=True(既定)の場合、適用直前の書込
    レイヤを記憶しておき、適用後に`utils.line_attr_dialog.
    set_layer_group()`(右クリック切替、既存の安全な仕組み)で元へ戻す
    ことで、体感上は書込レイヤが動かないようにする。keep_write_layer=
    Falseなら、この後処理をせず、JWLに書かれた保存時点の書込レイヤへ
    素直に切り替わる(ユーザー要望でボタンごとに選べるようにした、
    2026-09-07)。
    戻り値: 成功したらTrue。"""
    def _log(msg):
        if log:
            try:
                log(msg)
            except Exception:
                pass

    if not jwl_path or not os.path.isfile(jwl_path):
        return False

    orig_group, orig_layer = (None, None)
    if keep_write_layer:
        orig_group, orig_layer = line_attr_dialog.read_current_layer_group(hwnd)

    before = set()

    def cb(h, _extra):
        try:
            if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "#32770":
                before.add(h)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumWindows(cb, None)
    except Exception:
        pass

    force_foreground(hwnd)
    time.sleep(0.2)
    win32gui.PostMessage(hwnd, win32con.WM_COMMAND, win32api.MAKELONG(LOAD_CONFIG_CMD_ID, 0), 0)
    _log("[レイヤ復元詳細] 環境設定ファイル読込みコマンド送信")

    dlg = _find_new_window("#32770", before, timeout=2.0)
    if not dlg:
        _log("❌[レイヤ復元詳細] 「開く」ダイアログが見つかりません")
        return False
    _log("[レイヤ復元詳細] 「開く」ダイアログ検出")

    edits = _find_children(dlg, "Edit")
    buttons = _find_children(dlg, "Button")
    if not edits or not buttons:
        _log("❌[レイヤ復元詳細] ダイアログ内のEdit/Buttonが見つかりません")
        return False

    # 👑 ファイル名欄は複数あるEditのうち、ダイアログ内で最もy座標が
    # 大きい(下寄りの)もの。実機確認(2026-09-04): アドレスバーのEditは
    # 上部、ファイル名欄は下部(Open/Cancelボタンのすぐ上)にある。
    def top_y(h):
        try:
            return win32gui.GetWindowRect(h)[1]
        except Exception:
            return -1

    filename_edit = max(edits, key=top_y)
    win32gui.SendMessage(filename_edit, win32con.WM_SETTEXT, 0, jwl_path)
    _log("[レイヤ復元詳細] ファイル名欄に設定")

    open_btn = None
    for b in buttons:
        try:
            text = win32gui.GetWindowText(b)
        except Exception:
            text = ""
        if "開く" in text:
            open_btn = b
            break
    if not open_btn:
        open_btn = buttons[0]
    win32gui.PostMessage(open_btn, win32con.BM_CLICK, 0, 0)
    _log("[レイヤ復元詳細] 「開く」クリック送信")

    if orig_group is not None and orig_layer is not None:
        # 👑 JWL読み込みが実際に反映されるまで一瞬かかるため、少し待って
        # から元の書込レイヤへ戻す(早すぎるとread_current_layer_group()が
        # 反映前の値を読んでしまい、set_layer_group()が「既に選択中」と
        # 誤判定してレイヤ一覧ダイアログを開いてしまう恐れがある)。
        time.sleep(0.8)
        line_attr_dialog.set_layer_group(hwnd, group=orig_group, layer=orig_layer)
        _log(f"[レイヤ復元詳細] 書込レイヤを元へ復帰 group={orig_group} layer={orig_layer}")

    return True
# ===== ✂️ utils/layer_snapshot.py END ✂️ =====
