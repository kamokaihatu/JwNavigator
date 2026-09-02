# ===== ✂️ utils/line_attr_dialog.py START ✂️ =====
"""
jw_cad標準の「線属性」ダイアログ(idCommand=32807、コマンドC047)を
自動操作する。線色9個(線色1〜8＋補助線色)・線種9個(実線〜二点鎖2＋
補助線種)・線幅入力欄を持つ、標準の#32770ダイアログ。

👑 このダイアログの子コントロールのhwndは開き直すたびに変わる(実機で
確認済み)。ctrl_id(GWL_ID)は固定なので、開くたびにEnumChildWindowsで
ctrl_id→hwndの対応表を作り直す。詳しい調査経緯はdoc/シート管理_設計
メモ.mdおよびdoc/補助線ボタン_要件書.mdを参照。

「補助線」「配線」ボタン(kind="auto_attr")の実装で使う。標準のMFC
ダイアログなのでBM_CLICK/BM_GETSTATE/WM_SETTEXT/WM_GETTEXTのみで完結し、
SB_GETTEXTWのような危険な分岐(クロスプロセス手動マーシャリングが必要)
は無い。
"""
import ctypes
import re
import time

import win32api
import win32con
import win32gui
import win32process

from utils.send_key import force_foreground_window

WM_COMMAND = 0x0111
BM_CLICK = 0x00F5
BM_GETSTATE = 0x00F2
BST_PUSHED = 0x0004
ID_COMMAND_LINE_ATTR = 32807

# 線色1〜8 + 補助線色(9番目)。線種は実線〜二点鎖2 + 補助線種(9番目)。
COLOR_CTRL_IDS = [1401, 1402, 1403, 1404, 1405, 1406, 1407, 1408, 1409]
TYPE_CTRL_IDS = [2449, 2450, 2451, 2452, 2453, 2454, 2455, 2456, 2457]
COLOR_LABELS = ["線色1", "線色2", "線色3", "線色4", "線色5", "線色6", "線色7", "線色8", "補助線色"]
TYPE_LABELS = ["実線", "点線1", "点線2", "点線3", "一点鎖1", "一点鎖2", "二点鎖1", "二点鎖2", "補助線種"]

WIDTH_EDIT_ID = 2224
OK_CTRL_ID = 1
CANCEL_CTRL_ID = 2

DEFAULT_COLOR_CTRL_ID = 1409  # 補助線色
DEFAULT_TYPE_CTRL_ID = 2457   # 補助線種


def _find_dialog_hwnd(timeout=0.6):
    deadline = time.time() + timeout
    while time.time() < deadline:
        found = []

        def cb(hwnd, _extra):
            try:
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) == "線属性":
                    found.append(hwnd)
            except Exception:
                pass
            return True

        try:
            win32gui.EnumWindows(cb, None)
        except Exception:
            pass
        if found:
            return found[0]
        time.sleep(0.03)
    return None


def _build_ctrl_map(dialog_hwnd):
    ctrl_map = {}

    def cb(child, _extra):
        try:
            ctrl_id = win32api.GetWindowLong(child, win32con.GWL_ID)
            ctrl_map[ctrl_id] = child
        except Exception:
            pass
        return True

    try:
        win32gui.EnumChildWindows(dialog_hwnd, cb, None)
    except Exception:
        pass
    return ctrl_map


def _find_pushed(ctrl_map, ctrl_ids):
    for cid in ctrl_ids:
        h = ctrl_map.get(cid)
        if h is None:
            continue
        try:
            state = win32gui.SendMessage(h, BM_GETSTATE, 0, 0)
        except Exception:
            continue
        if state & BST_PUSHED:
            return cid
    return None


def _open_dialog(hwnd):
    force_foreground_window(hwnd)
    time.sleep(0.05)
    wparam = win32api.MAKELONG(ID_COMMAND_LINE_ATTR, 0)
    win32gui.PostMessage(hwnd, WM_COMMAND, wparam, 0)
    dlg = _find_dialog_hwnd()
    if dlg:
        # 👑 JwNavigator自身のパレットは常時topmostでjw_cadの上に固定
        # されているため、線属性ダイアログの右側(線色ボタン群)がその
        # パレットに隠れてしまい、見本読み取り(GetPixel)で自分自身の
        # パレットの色を読んでしまう不具合が実機で発覚した(線種は中央
        # 寄りで隠れず正しく読めていたが、線色だけ空振りしていた)。
        # ダイアログ自体を一時的にHWND_TOPMOSTへ引き上げ、確実に最前面
        # にしてから読み取る。
        try:
            win32gui.SetWindowPos(
                dlg, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
            )
        except Exception:
            pass
    return dlg


def read_current_attr(hwnd):
    """線属性ダイアログを開いて今の設定を読み取り、変更せずキャンセルで
    閉じる。戻り値: {"color": ctrl_id, "type": ctrl_id, "width": str}
    (読み取り失敗時はNone)。"""
    dlg = _open_dialog(hwnd)
    if not dlg:
        return None
    ctrl_map = _build_ctrl_map(dlg)
    color = _find_pushed(ctrl_map, COLOR_CTRL_IDS)
    ltype = _find_pushed(ctrl_map, TYPE_CTRL_IDS)
    width = ""
    if WIDTH_EDIT_ID in ctrl_map:
        try:
            width = win32gui.GetWindowText(ctrl_map[WIDTH_EDIT_ID])
        except Exception:
            width = ""
    if CANCEL_CTRL_ID in ctrl_map:
        win32gui.SendMessage(ctrl_map[CANCEL_CTRL_ID], BM_CLICK, 0, 0)
        time.sleep(0.05)
    return {"color": color, "type": ltype, "width": width}


HV_BUTTON_TEXT = "水平･垂直"
BST_CHECKED = 0x0001


def _find_hv_ctrl(hwnd):
    # 👑 「水平･垂直」は線属性ダイアログとは別物で、直線コマンドが
    # アクティブな間だけ画面上部の「条件設定」バーに実在するコンテキスト
    # 依存のコントロール（実機確認: ctrl_id=1333、BST_CHECKEDで状態を
    # 持つチェックボックス、線属性ダイアログの線色/線種ボタン(BST_PUSHED
    # を使うラジオ風)とはビットが異なる）。hwnd自体が変わりうるため毎回
    # テキストで探し直す。
    found = []

    def cb(child, _extra):
        try:
            if win32gui.GetWindowText(child) == HV_BUTTON_TEXT:
                found.append(child)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumChildWindows(hwnd, cb, None)
    except Exception:
        pass
    return found[0] if found else None


def set_horizontal_vertical(hwnd, enabled):
    """条件設定バーの「水平･垂直」チェックを指定の状態にする。直線コマンド
    に切り替わった直後でないと見つからない(コンテキスト依存)。
    戻り値: 操作できたらTrue、コントロールが見つからなければFalse。"""
    ctrl = _find_hv_ctrl(hwnd)
    if not ctrl:
        return False
    try:
        state = win32gui.SendMessage(ctrl, BM_GETSTATE, 0, 0)
    except Exception:
        return False
    is_checked = bool(state & BST_CHECKED)
    if is_checked != bool(enabled):
        win32gui.SendMessage(ctrl, BM_CLICK, 0, 0)
    return True


def apply_attr(hwnd, color_ctrl_id=None, type_ctrl_id=None, width_text=None):
    """線属性ダイアログを開いて指定の線色・線種(・線幅)に変更し、OKで
    確定する。各引数がNoneの項目は変更しない(現状維持)。
    戻り値: 成功したらTrue。"""
    dlg = _open_dialog(hwnd)
    if not dlg:
        return False
    ctrl_map = _build_ctrl_map(dlg)

    if color_ctrl_id and color_ctrl_id in ctrl_map:
        win32gui.SendMessage(ctrl_map[color_ctrl_id], BM_CLICK, 0, 0)
        time.sleep(0.03)
    if type_ctrl_id and type_ctrl_id in ctrl_map:
        win32gui.SendMessage(ctrl_map[type_ctrl_id], BM_CLICK, 0, 0)
        time.sleep(0.03)
    if width_text is not None and WIDTH_EDIT_ID in ctrl_map:
        win32gui.SendMessage(ctrl_map[WIDTH_EDIT_ID], win32con.WM_SETTEXT, 0, width_text)
        time.sleep(0.03)

    if OK_CTRL_ID not in ctrl_map:
        return False
    win32gui.SendMessage(ctrl_map[OK_CTRL_ID], BM_CLICK, 0, 0)
    time.sleep(0.1)
    return True


# ---- レイヤ/レイヤグループ切替 ----
# 👑 実機調査の末に判明(doc/シート管理_設計メモ.md参照): レイヤ/レイヤ
# グループのボタン群(各16個、0〜F)は左クリック(BM_CLICK)だと表示状態
# (編集可→非表示→表示)を循環させるだけの別機能で、実際にレイヤ/グループを
# 切り替えるのは右クリック(WM_RBUTTONDOWN+WM_RBUTTONUP)。16個全てが
# 同じctrl_id(33038)を共有していて区別できないため、画面上の位置
# (rectのx,y)でソートして0〜Fを特定する。グループを切り替えるとその
# グループ内のレイヤ選択は0にリセットされる(実機確認済み)。

LAYER_GROUP_CTRL_ID = 33038
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
SB_GETTEXTW = 0x040D
_PROCESS_VM_ACCESS = (
    win32con.PROCESS_VM_OPERATION | win32con.PROCESS_VM_READ
    | win32con.PROCESS_VM_WRITE | win32con.PROCESS_QUERY_INFORMATION
)


def _find_layer_group_buttons(hwnd):
    """戻り値: (layer_hwnds[16], group_hwnds[16])。見つからなければ
    (None, None)。hwnd自体は実行のたびに変わるので毎回列挙し直す。"""
    found = []

    def cb(child, _extra):
        try:
            if win32api.GetWindowLong(child, win32con.GWL_ID) != LAYER_GROUP_CTRL_ID:
                return True
            # 👑 「All」ボタン(全レイヤ表示切替、別機能)も同じctrl_idを
            # 共有している(実機確認)。0〜Fの16個グリッドとは別物なので、
            # テキストで除外する。
            if win32gui.GetWindowText(child) == "All":
                return True
            rect = win32gui.GetWindowRect(child)
            found.append((child, rect[0], rect[1]))
        except Exception:
            pass
        return True

    try:
        win32gui.EnumChildWindows(hwnd, cb, None)
    except Exception:
        pass
    if len(found) != 32:
        return None, None
    found.sort(key=lambda item: (item[1], item[2]))
    layer_hwnds = [item[0] for item in found[:16]]
    group_hwnds = [item[0] for item in found[16:]]
    return layer_hwnds, group_hwnds


def _right_click(target_hwnd, hwnd_for_foreground):
    force_foreground_window(hwnd_for_foreground)
    time.sleep(0.05)
    l, t, r, b = win32gui.GetWindowRect(target_hwnd)
    w_, h_ = r - l, b - t
    lparam = win32api.MAKELONG(w_ // 2, h_ // 2)
    win32gui.SendMessage(target_hwnd, WM_RBUTTONDOWN, 0, lparam)
    time.sleep(0.05)
    win32gui.SendMessage(target_hwnd, WM_RBUTTONUP, 0, lparam)
    time.sleep(0.05)


def set_layer_group(hwnd, group=None, layer=None):
    """指定のレイヤグループ・レイヤ番号(0〜15、A〜Fは10〜15)へ右クリックで
    切り替える。groupだけ/layerだけの指定も可(Noneの項目は変更しない)。
    両方指定する場合はグループを切り替えるとレイヤが0にリセットされる
    ため、グループ→レイヤの順で切り替える。
    戻り値: 操作できたらTrue。
    👑 **重大**: 既に選択中のグループ/レイヤのボタンを右クリックすると、
    切替は起きず代わりに「レイヤ一覧」「レイヤグループ一覧」という管理
    ダイアログが開いてしまう(実機確認済み、意図しないダイアログが残る
    副作用があった)。そのため、目標が現在値と同じ場合はクリックせず
    スキップする。"""
    layer_hwnds, group_hwnds = _find_layer_group_buttons(hwnd)
    if layer_hwnds is None:
        return False
    cur_group, cur_layer = read_current_layer_group(hwnd)
    if group is not None:
        if not (0 <= group <= 15):
            return False
        if group != cur_group:
            _right_click(group_hwnds[group], hwnd)
            time.sleep(0.15)
            # 👑 グループ切替後のレイヤ番号は0とは限らない挙動が実機で
            # 見られた(想定と食い違うと、次のレイヤ右クリックが「既に
            # 選択中のボタン」と誤判定され一覧ダイアログが開いてしまう)。
            # 推測に頼らず、切替後の実際の値を読み直す。
            _, cur_layer = read_current_layer_group(hwnd)
    if layer is not None:
        if not (0 <= layer <= 15):
            return False
        if layer != cur_layer:
            _right_click(layer_hwnds[layer], hwnd)
    return True


def _find_statusbar(hwnd):
    found = []

    def cb(child, _extra):
        if "statusbar" in win32gui.GetClassName(child).lower():
            found.append(child)
        return True

    try:
        win32gui.EnumChildWindows(hwnd, cb, None)
    except Exception:
        pass
    return found[0] if found else None


def _read_statusbar_part(sb_hwnd, part_index, buf_chars=256):
    # 👑 SB_GETTEXTWはクロスプロセスで自動マーシャリングされないため、
    # VirtualAllocExで対象プロセス内にバッファを確保し、結果を
    # ReadProcessMemoryで読み戻す必要がある(doc/シート管理_設計メモ.md、
    # 「重大な注意」参照。素通りするとjw_cadをクラッシュさせた実績あり)。
    _, pid = win32process.GetWindowThreadProcessId(sb_hwnd)
    hproc = win32api.OpenProcess(_PROCESS_VM_ACCESS, False, pid)
    if not hproc:
        return None
    try:
        size = buf_chars * 2
        remote_addr = ctypes.windll.kernel32.VirtualAllocEx(
            int(hproc), None, size, win32con.MEM_COMMIT, win32con.PAGE_READWRITE
        )
        if not remote_addr:
            return None
        try:
            win32gui.SendMessage(sb_hwnd, SB_GETTEXTW, part_index, remote_addr)
            local_buf = ctypes.create_unicode_buffer(buf_chars)
            n_read = ctypes.c_size_t(0)
            ok = ctypes.windll.kernel32.ReadProcessMemory(
                int(hproc), ctypes.c_void_p(remote_addr), local_buf, size, ctypes.byref(n_read)
            )
            if not ok:
                return None
            return local_buf.value
        finally:
            ctypes.windll.kernel32.VirtualFreeEx(int(hproc), ctypes.c_void_p(remote_addr), 0, win32con.MEM_RELEASE)
    finally:
        win32api.CloseHandle(hproc)


def read_current_layer_group(hwnd):
    """ステータスバーのパート3(`[グループ-レイヤ]レイヤ名`)から現在の
    グループ番号・レイヤ番号を読む(0〜15)。読み取れなければ(None, None)。"""
    sb = _find_statusbar(hwnd)
    if not sb:
        return None, None
    text = _read_statusbar_part(sb, 3)
    if not text:
        return None, None
    m = re.match(r"\s*\[([0-9A-Fa-f])-([0-9A-Fa-f])\]", text)
    if not m:
        return None, None
    return int(m.group(1), 16), int(m.group(2), 16)


# ---- 見本画面用: 実機の線属性ダイアログから色/線種を実際に読み取る ----
# 👑 「線種決めるのに、jwのシステムは使えないよねー」への対応。線属性
# ダイアログを開いて閉じるだけの読み取り専用操作(変更しない)で、各
# ボタンの実際のピクセル色・線種パターンをGetPixelで読み取り、jw_cad
# 本体そっくりの見本をJwNavigator側にも表示できるようにする。実機確認
# 済み(線色は中心1点、線種は複数行×複数列でオン/オフパターンを判定)。

TYPE_PATTERN_SAMPLES = 24  # 線種パターンを何点にサンプリングするか


def _rgb_to_hex(pixel):
    r = pixel & 0xFF
    g = (pixel >> 8) & 0xFF
    b = (pixel >> 16) & 0xFF
    return f"#{r:02x}{g:02x}{b:02x}"


def capture_swatches(hwnd, on_color=None, on_type=None):
    """線属性ダイアログを開いて色9個・線種9個の実際の見本を読み取り、
    変更せずキャンセルで閉じる。戻り値:
    {"colors": [(ctrl_id, "#rrggbb"), ...], "types": [(ctrl_id, [bool,...]), ...]}
    (読み取り失敗時はNone)。
    👑 on_color(ctrl_id, hex_color)/on_type(ctrl_id, pattern)を渡すと、
    1項目読み取るたびに都度呼ばれる(「読めたもの1個ずつ更新していけたら
    臨場感あるけどできそう？」への対応。呼び出し元がTkinterのメイン
    スレッドから同期的に呼ぶ前提で、別スレッド化はしていない)。"""
    dlg = _open_dialog(hwnd)
    if not dlg:
        return None
    ctrl_map = _build_ctrl_map(dlg)
    # 👑 ダイアログのhwndが見つかった直後は、中の18個のプレビュー(色9+
    # 線種9)がまだ描画し切れていないことがある(実機で、同じ条件でも
    # 読み取り結果が実行のたびにバラつくのを確認)。GetPixelで読む前に
    # 実際に描き終わるのを少し待つ。
    time.sleep(0.25)
    hdc = win32gui.GetDC(0)
    try:
        # 👑 jw_cadが直線コマンド等の入力待ち(始点/次点クリック待ち)の
        # 最中に線属性ダイアログを自動で開くと、読み取り中にダイアログの
        # 子コントロールが無効になり(実機確認: 例外「ウィンドウ ハンドル
        # が無効です」)、そのまま丸ごと読み取り失敗になっていた。1個の
        # コントロール失敗で全体を巻き込まないよう、個別にtry/exceptで
        # 守り、失敗した項目だけ既定値にフォールバックする。
        colors = []
        for cid in COLOR_CTRL_IDS:
            h = ctrl_map.get(cid)
            if not h:
                hex_color = "#f0f0f0"
            else:
                try:
                    rect = win32gui.GetWindowRect(h)
                    cx = (rect[0] + rect[2]) // 2
                    cy = (rect[1] + rect[3]) // 2
                    hex_color = _rgb_to_hex(win32gui.GetPixel(hdc, cx, cy))
                except Exception:
                    hex_color = "#f0f0f0"
            colors.append((cid, hex_color))
            if on_color:
                on_color(cid, hex_color)
                time.sleep(0.08)

        types = []
        for cid in TYPE_CTRL_IDS:
            h = ctrl_map.get(cid)
            if not h:
                pattern = [False] * TYPE_PATTERN_SAMPLES
                types.append((cid, pattern))
                if on_type:
                    on_type(cid, pattern)
                    time.sleep(0.08)
                continue
            try:
                rect = win32gui.GetWindowRect(h)
            except Exception:
                pattern = [False] * TYPE_PATTERN_SAMPLES
                types.append((cid, pattern))
                if on_type:
                    on_type(cid, pattern)
                    time.sleep(0.08)
                continue
            x0, x1 = rect[0] + 3, rect[2] - 3
            ys = [
                rect[1] + (rect[3] - rect[1]) // 2 - 1,
                rect[1] + (rect[3] - rect[1]) // 2,
                rect[1] + (rect[3] - rect[1]) // 2 + 1,
            ]
            width = max(1, x1 - x0)
            # 👑 「基本設定の色を見てこないと個人で違うかも」というユーザー
            # 指摘への対応。以前は「暗い=線あり」という固定しきい値だった
            # ため、背景が濃い色(ダーク系の基本設定)のユーザーだと反転して
            # 誤判定していた。ボタンの左端(パターンが届く前の余白、実機で
            # 常に背景のみと確認済み)を毎回サンプリングして背景色を基準に
            # し、そこから明確に離れた色を「線あり」とする相対判定に変更。
            bg_pixel = win32gui.GetPixel(hdc, rect[0] + 1, ys[1])
            bg_r, bg_g, bg_b = bg_pixel & 0xFF, (bg_pixel >> 8) & 0xFF, (bg_pixel >> 16) & 0xFF
            pattern = []
            for i in range(TYPE_PATTERN_SAMPLES):
                x = x0 + int(width * i / TYPE_PATTERN_SAMPLES)
                is_drawn = False
                for y in ys:
                    pixel = win32gui.GetPixel(hdc, x, y)
                    r = pixel & 0xFF
                    g = (pixel >> 8) & 0xFF
                    b = (pixel >> 16) & 0xFF
                    diff = abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b)
                    if diff > 60:
                        is_drawn = True
                        break
                pattern.append(is_drawn)
            types.append((cid, pattern))
            if on_type:
                on_type(cid, pattern)
                time.sleep(0.08)
    finally:
        win32gui.ReleaseDC(0, hdc)

    if CANCEL_CTRL_ID in ctrl_map:
        win32gui.SendMessage(ctrl_map[CANCEL_CTRL_ID], BM_CLICK, 0, 0)
        time.sleep(0.05)

    return {"colors": colors, "types": types}
# ===== ✂️ utils/line_attr_dialog.py END ✂️ =====
