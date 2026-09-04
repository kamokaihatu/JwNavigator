# ===== ✂️ utils/layer_snapshot.py START ✂️ =====
"""
「電灯配線図」のようなレイヤ状態の保存/復元ボタン用の自動化。
doc/シート管理_設計メモ.md, doc/HANDOFF_layer_control.md参照。

保存: jw_cad側に外部変形(A_SAVE.bat)をCtrl+<SAVE_KEY>のキー割り付け
(GCOM_100、config/keybind_setup.md参照)で登録しておき、そのキーを合成
送信するだけで起動する(外部変形自体のファイル選択ダイアログは独自の
owner-drawツリーで自動操作できないため、キー割り付け経由で迂回する)。
起動後は「小さい範囲を1回ドラッグして選択確定」という操作だけユーザーに
残る。完了するとjw_cad実行フォルダ直下にLAYER_RESTORE.JWLが生成/更新
されるので、そのmtimeの変化を監視して完了を検知し、ボタン専用のファイル
にコピーする。

復元: 「設定→環境設定ファイル→読込み」(idCommand=32923)は標準の
Windows「開く」ダイアログを開くため、ファイル名欄への直接WM_SETTEXTと
「開く」ボタンのBM_CLICKだけで完全に無人実行できる(実機確認済み)。
"""
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
LOAD_CONFIG_CMD_ID = 32923  # 設定→環境設定ファイル→読込み


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


def _find_button_by_text(hwnd, text, timeout=1.5):
    # 👑 範囲選択中に現れる「全選択」「選択確定」はowner-drawではない
    # 普通のButtonコントロールで、BM_CLICKに反応することを実機確認済み
    # (2026-09-04)。出現が選択モード開始と非同期のため、少し待って
    # ポーリングする。
    deadline = time.time() + timeout
    while time.time() < deadline:
        found = []

        def cb(h, _extra):
            try:
                if win32gui.GetClassName(h) == "Button" and win32gui.GetWindowText(h) == text:
                    found.append(h)
            except Exception:
                pass
            return True

        try:
            win32gui.EnumChildWindows(hwnd, cb, None)
        except Exception:
            pass
        if found:
            return found[0]
        time.sleep(0.1)
    return None


def trigger_save(hwnd):
    """Ctrl+<SAVE_KEY>を送ってA_SAVE.batを起動し、続けて「全選択」→
    「選択確定」を自動クリックする(ユーザーのドラッグ操作を不要にする、
    2026-09-04実機確認済み)。図面全体が対象になるため、大きい図面では
    jwc_temp.txtの書き出しに時間がかかる可能性がある。
    戻り値: {"jwl_path":.., "baseline_mtime":..} (完了検知に使う)。
    jwl_pathが取得できなければNoneを返す。"""
    path = restore_jwl_path(hwnd)
    if not path:
        return None
    baseline = None
    if os.path.isfile(path):
        try:
            baseline = os.path.getmtime(path)
        except OSError:
            baseline = None
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    time.sleep(0.2)
    win32api.keybd_event(VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(SAVE_KEY_VK, 0, 0, 0)
    win32api.keybd_event(SAVE_KEY_VK, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

    select_all_btn = _find_button_by_text(hwnd, "全選択")
    if select_all_btn:
        win32gui.PostMessage(select_all_btn, win32con.BM_CLICK, 0, 0)
        time.sleep(0.3)
        confirm_btn = _find_button_by_text(hwnd, "選択確定")
        if confirm_btn:
            win32gui.PostMessage(confirm_btn, win32con.BM_CLICK, 0, 0)

    return {"jwl_path": path, "baseline_mtime": baseline}


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


def trigger_restore(hwnd, jwl_path):
    """「設定→環境設定ファイル→読込み」を自動実行し、jwl_pathを読み込ませる。
    実機確認済み(標準の「開く」コモンダイアログのため自動操作可能)。

    👑 JWLは書込レイヤグループ/レイヤを保存時点の値へ強制的に動かして
    しまう(`100`指定を省くと逆にファイル全体が無視されると実機で判明、
    2026-09-04)。ユーザー提案により、適用直前の書込レイヤを記憶して
    おき、適用後に`utils.line_attr_dialog.set_layer_group()`(右クリック
    切替、既存の安全な仕組み)で元へ戻すことで、体感上は書込レイヤが
    動かないようにする。
    戻り値: 成功したらTrue。"""
    if not jwl_path or not os.path.isfile(jwl_path):
        return False

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

    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    time.sleep(0.2)
    win32gui.PostMessage(hwnd, win32con.WM_COMMAND, win32api.MAKELONG(LOAD_CONFIG_CMD_ID, 0), 0)

    dlg = _find_new_window("#32770", before, timeout=2.0)
    if not dlg:
        return False

    edits = _find_children(dlg, "Edit")
    buttons = _find_children(dlg, "Button")
    if not edits or not buttons:
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

    if orig_group is not None and orig_layer is not None:
        # 👑 JWL読み込みが実際に反映されるまで一瞬かかるため、少し待って
        # から元の書込レイヤへ戻す(早すぎるとread_current_layer_group()が
        # 反映前の値を読んでしまい、set_layer_group()が「既に選択中」と
        # 誤判定してレイヤ一覧ダイアログを開いてしまう恐れがある)。
        time.sleep(0.8)
        line_attr_dialog.set_layer_group(hwnd, group=orig_group, layer=orig_layer)

    return True
# ===== ✂️ utils/layer_snapshot.py END ✂️ =====
