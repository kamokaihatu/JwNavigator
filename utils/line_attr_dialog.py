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
import threading
import time

import win32api
import win32con
import win32gui
import win32process

from utils.send_key import force_foreground_window
from utils import diagnostics

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

# 👑 2026-09-24: 外部から受け取った図面が「SXF対応拡張線色・線種」に
# なっていると、線属性ダイアログが丸ごと別物になる(実機ダンプで確定、
# tools/dump_line_attr_dialog.py で再取得できる)。
#
#   既定モード: コントロール44個、線色1401〜1409、線種2449〜2457、キャンセルあり
#   SXFモード : コントロール75個、線色2268〜2283、線種2449〜2464、**キャンセル無し**
#
# ここには罠が2つある。
#  (1) **線種のIDが重なる**。既定の「補助線種=2457」はSXFモードでは「9番=点線」。
#      つまりIDの有無でモードを判別してはいけない。必ずSXF_CHECKBOX_IDの
#      チェック状態で判別する。判別せずに送ると、黙って意図しない線種に変わる。
#  (2) SXFモードには**キャンセルボタンが無い**。読み取りだけのつもりで開くと
#      閉じられず、モーダルのままjw_cadが操作不能になる(kamo報告「モード
#      ボタンおしたらとまっちゃった」の直接原因)。_close_after_read()を使う。
SXF_CHECKBOX_ID = 2312
SXF_COLOR_CTRL_IDS = list(range(2268, 2284))   # 1〜16番
SXF_TYPE_CTRL_IDS = list(range(2449, 2465))    # 1〜16番
BM_GETCHECK = 0x00F0
BM_SETCHECK = 0x00F1


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
            diagnostics.ok("線属性ダイアログ")
            return found[0]
        time.sleep(0.03)
    # 👑 2026-09-16: ここでNoneを返すとread_current_attr()/apply_attr()が
    # 揃って失敗し、モードボタンが「押しても何も起きない」状態になる。
    # 今までは黙ってNoneだったため原因が追えなかったので記録する。
    diagnostics.note(
        "線属性ダイアログ",
        f"{timeout}秒待っても開きませんでした"
        "(モードボタンの線属性切替が働きません)",
    )
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
    except Exception as e:
        diagnostics.note("線属性ダイアログの中身", f"列挙に失敗しました: {e}")
        return ctrl_map
    # 👑 2026-09-16: 空やOKボタン欠けは「ダイアログは開いたのに操作できない」
    # 状態で、apply_attr()が黙ってFalseを返すだけになる。
    if OK_CTRL_ID not in ctrl_map:
        diagnostics.note(
            "線属性ダイアログの中身",
            f"OKボタン(ctrl_id={OK_CTRL_ID})が見つかりません"
            f"(検出したコントロール数={len(ctrl_map)})",
        )
    else:
        diagnostics.ok("線属性ダイアログの中身", f"コントロール{len(ctrl_map)}個")
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


def read_sxf_mode(ctrl_map):
    """「SXF対応拡張線色・線種」のチェック状態を返す。
    True=ON / False=OFF / None=チェックボックス自体が無い(この環境の
    線属性ダイアログにSXFの概念が無い、または列挙に失敗した)。
    👑 Noneと**Falseを区別する**こと。Noneのときに「OFFにする」操作を
    しようとしても対象が無いので、黙って成功と言ってはいけない。"""
    h = ctrl_map.get(SXF_CHECKBOX_ID)
    if h is None:
        return None
    try:
        return bool(win32gui.SendMessage(h, BM_GETCHECK, 0, 0))
    except Exception:
        return None


def _set_sxf_mode(dlg, ctrl_map, enabled):
    """SXFのチェックを指定の状態にする。戻り値: (dlg, ctrl_map, ok)。

    👑 2026-09-24 実機で判明: チェックを押すとjw_cadは**ダイアログを丸ごと
    作り直す**。中身が入れ替わるのではなくHWND自体が変わり、古いハンドルは
    無効になる(ログ: 古いhwndでの列挙が「コントロール0個」、PostMessageが
    「(1400, 'PostMessage', 'ウィンドウ ハンドルが無効です。')」)。よって
    子の再列挙だけでは足りず、**ダイアログを探し直す**必要がある。

    ok=False は「頼まれた状態にできたと確認できなかった」。線種はIDが
    重なっているので、確認できないまま押すと別の線種に変わってしまう。
    呼び出し側は必ず中止すること。なお**チェックボックス自体が無い環境**
    (SXFの概念が無い古いjw_cad)は、何もしなくても既定モードなので
    enabled=Falseならok=Trueで返す。"""
    current = read_sxf_mode(ctrl_map)
    if current is None:
        # SXFの概念が無いダイアログ。OFFを頼まれているなら既に目的の状態。
        return dlg, ctrl_map, not enabled
    if bool(current) == bool(enabled):
        return dlg, ctrl_map, True

    win32gui.SendMessage(ctrl_map[SXF_CHECKBOX_ID], BM_CLICK, 0, 0)
    time.sleep(0.15)
    new_dlg = _find_dialog_hwnd() or dlg
    if new_dlg != dlg:
        # 作り直された新しいダイアログも、見本読み取りのために最前面へ
        # 引き上げておく(_open_dialog内の同じ処理と同じ理由)。
        try:
            win32gui.SetWindowPos(
                new_dlg, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
            )
        except Exception:
            pass
    new_map = _build_ctrl_map(new_dlg)
    after = read_sxf_mode(new_map)
    if after is None or bool(after) != bool(enabled):
        diagnostics.note(
            "線属性ダイアログのSXF切替",
            f"SXF対応を{'ON' if enabled else 'OFF'}にできたか確認できません"
            f"(切替後のダイアログ: hwnd={new_dlg}, コントロール{len(new_map)}個, "
            f"SXF={'ON' if after else 'OFF' if after is not None else '読めず'})",
        )
        return new_dlg, new_map, False
    diagnostics.ok("線属性ダイアログのSXF切替", f"SXF対応を{'ON' if enabled else 'OFF'}にしました")
    return new_dlg, new_map, True


def _close_after_read(dlg, ctrl_map):
    """読み取りだけで開いたダイアログを閉じる。
    👑 SXFモードにはキャンセル(ctrl_id=2)が無いのでWM_CLOSEで閉じる。
    OKを押してはいけない(今表示されている内容を適用してしまう)。"""
    if CANCEL_CTRL_ID in ctrl_map:
        try:
            win32gui.SendMessage(ctrl_map[CANCEL_CTRL_ID], BM_CLICK, 0, 0)
            time.sleep(0.05)
            return True
        except Exception:
            pass
    try:
        win32gui.PostMessage(dlg, win32con.WM_CLOSE, 0, 0)
        time.sleep(0.05)
        return True
    except Exception as e:
        # 👑 2026-09-24: 渡されたhwndが既に無効なことがある(SXFの切替で
        # ダイアログが作り直された後など)。ここで諦めるとモーダルのまま
        # 残ってjw_cadが操作不能になるので、開いているものを探し直して
        # もう一度閉じにいく。
        again = _find_dialog_hwnd(timeout=0.3)
        if again and again != dlg:
            try:
                win32gui.PostMessage(again, win32con.WM_CLOSE, 0, 0)
                time.sleep(0.05)
                diagnostics.note(
                    "線属性ダイアログの後始末",
                    f"渡されたhwndが無効だったため探し直して閉じました({e})",
                )
                return True
            except Exception:
                pass
        diagnostics.note(
            "線属性ダイアログの後始末",
            f"閉じられませんでした({e})。モーダルのまま残るとjw_cadが操作できません",
        )
        return False


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
    """線属性ダイアログを開いて今の設定を読み取り、変更せず閉じる。
    戻り値: {"color": ctrl_id, "type": ctrl_id, "width": str, "sxf": bool|None}
    (ダイアログが開けなかった場合のみNone)。

    👑 "color"/"type"のctrl_idは **"sxf"とセットでしか意味を持たない**。
    SXFモードでは線色のIDが別の並びになり、しかも線種はIDが重なって
    意味だけが違う(SXF_CHECKBOX_ID付近のコメント参照)。apply_attr()へ
    戻すときは必ずsxfも一緒に渡すこと。"""
    dlg = _open_dialog(hwnd)
    if not dlg:
        return None
    ctrl_map = _build_ctrl_map(dlg)
    sxf = read_sxf_mode(ctrl_map)
    color_ids = SXF_COLOR_CTRL_IDS if sxf else COLOR_CTRL_IDS
    type_ids = SXF_TYPE_CTRL_IDS if sxf else TYPE_CTRL_IDS
    color = _find_pushed(ctrl_map, color_ids)
    ltype = _find_pushed(ctrl_map, type_ids)
    width = ""
    if WIDTH_EDIT_ID in ctrl_map:
        try:
            width = win32gui.GetWindowText(ctrl_map[WIDTH_EDIT_ID])
        except Exception:
            width = ""
    # 👑 見つからなかったことを黙って空で返さない(2026-09-16の棚卸しの
    # 教訓。ここが「読めたつもりでNoneが入る」入口だった)。
    if color is None or ltype is None:
        missing = []
        if color is None:
            missing.append("線色")
        if ltype is None:
            missing.append("線種")
        diagnostics.note(
            "線属性の読み取り",
            f"{'/'.join(missing)}がどれも選択状態に見えません"
            f"(SXF対応={'ON' if sxf else 'OFF' if sxf is not None else '不明'}、"
            f"コントロール{len(ctrl_map)}個)",
        )
    else:
        diagnostics.ok(
            "線属性の読み取り",
            f"線色={color} 線種={ltype} (SXF対応={'ON' if sxf else 'OFF'})",
        )
    _close_after_read(dlg, ctrl_map)
    return {"color": color, "type": ltype, "width": width, "sxf": sxf}


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


def apply_attr(hwnd, color_ctrl_id=None, type_ctrl_id=None, width_text=None, sxf=None):
    """線属性ダイアログを開いて指定の線色・線種(・線幅)に変更し、OKで
    確定する。各引数がNoneの項目は変更しない(現状維持)。

    sxf: 「SXF対応拡張線色・線種」をこの状態にしてから指定する。
         False=既定モードのIDを使いたいとき / True=SXFモードのIDを使い
         たいとき / None=今のモードのまま触らない。
         👑 color_ctrl_id・type_ctrl_idは**sxfで指定したモードのID**で
         なければならない。モードが合っていないと、線種はIDが重なって
         いるため黙って別の線種を押してしまう。

    戻り値: 指定した項目を**実際に押せたら**True。押せなかった項目が
    あればFalse(理由はdiagnosticsへ)。👑 以前は何も変更できなくても
    OKを押してTrueを返していた(SXF図面で不具合になった)。"""
    dlg = _open_dialog(hwnd)
    if not dlg:
        return False
    ctrl_map = _build_ctrl_map(dlg)

    if sxf is not None:
        # 👑 切替でダイアログが作り直されるので、dlgごと受け取り直す。
        dlg, ctrl_map, mode_ok = _set_sxf_mode(dlg, ctrl_map, sxf)
        if not mode_ok:
            # 目的のモードにできたと確認できなかった。このまま押すと
            # 違う意味のIDを叩く(線種はIDが重なる)ので、何もせず閉じる。
            diagnostics.note(
                "線属性の変更",
                f"SXF対応を{'ON' if sxf else 'OFF'}にできたと確認できないため、"
                f"線属性の変更を中止しました(IDの意味が変わるため)",
            )
            _close_after_read(dlg, ctrl_map)
            return False

    missing = []
    if color_ctrl_id:
        if color_ctrl_id in ctrl_map:
            win32gui.SendMessage(ctrl_map[color_ctrl_id], BM_CLICK, 0, 0)
            time.sleep(0.03)
        else:
            missing.append(f"線色(ctrl_id={color_ctrl_id})")
    if type_ctrl_id:
        if type_ctrl_id in ctrl_map:
            win32gui.SendMessage(ctrl_map[type_ctrl_id], BM_CLICK, 0, 0)
            time.sleep(0.03)
        else:
            missing.append(f"線種(ctrl_id={type_ctrl_id})")
    if width_text is not None:
        if WIDTH_EDIT_ID in ctrl_map:
            win32gui.SendMessage(ctrl_map[WIDTH_EDIT_ID], win32con.WM_SETTEXT, 0, width_text)
            time.sleep(0.03)
        else:
            missing.append(f"線幅(ctrl_id={WIDTH_EDIT_ID})")

    if missing:
        diagnostics.note(
            "線属性の変更",
            f"{'、'.join(missing)}がこのダイアログに見つかりません"
            f"(SXF対応={'ON' if read_sxf_mode(ctrl_map) else 'OFF'}、"
            f"コントロール{len(ctrl_map)}個)",
        )
        _close_after_read(dlg, ctrl_map)
        return False

    if OK_CTRL_ID not in ctrl_map:
        _close_after_read(dlg, ctrl_map)
        return False
    win32gui.SendMessage(ctrl_map[OK_CTRL_ID], BM_CLICK, 0, 0)
    time.sleep(0.1)
    diagnostics.ok("線属性の変更", "指定した項目を反映しました")
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


# 👑 2026-09-16: レイヤ/レイヤグループのバーをどう見分けたかの記録。
# 名前で判別できず位置推定のフォールバックに落ちると、配置次第で両者が
# **丸ごと入れ替わる**(Ver3.73で直したはずの不具合が再発する)。しかし
# それがログに何も出ないと、今回のように「直したはずなのにまだ反転して
# いる?」の切り分けができない。呼び出し側(main.pyの環境スナップショット)
# から describe_layer_bar_detection() で吸い出せるようにしておく。
_last_bar_detection = "まだ判定していません"


def describe_layer_bar_detection():
    return _last_bar_detection


def _find_layer_group_buttons(hwnd):
    """戻り値: (layer_hwnds[16], group_hwnds[16])。見つからなければ
    (None, None)。hwnd自体は実行のたびに変わるので毎回列挙し直す。

    👑 2026-09-16: 32個のボタンは`ToolbarWindow32`の親2つに分かれている。
    どちらがレイヤでどちらがレイヤグループかの見分け方を2回間違えている:

      (1) 当初はx座標順に並べて前半/後半で決め打ちしていた。ツールバーの
          配置に依存するため、レイヤグループバーが左にあるPCでは**丸ごと
          入れ替わった**(kosakaPC:「F-Fにしたのに0-Fに描かれる」)。
      (2) Ver3.73で親のウィンドウテキスト("レイヤ"/"レイヤグループ")で
          判別するよう変えたが、**jw_cadはこのテキストを選択中の状態に
          応じて書き換える**(実機でグループFを選んだらキャプションが
          'F'になった)。そのため実際にはすぐフォールバックへ落ちて
          (1)の不具合が再発していた。

    今はツールバー自身の`GWL_ID`で判別する。これは利用者の操作では変化
    しない(実測: レイヤ=32854、レイヤグループ=32856)。番号を直接ハード
    コードせず**「小さい方がレイヤ、大きい方がレイヤグループ」**という
    順序で判定するので、jw_cadのバージョンが違って番号がずれても効く。
    バー内の0〜Fの並び順は従来どおり(x,y)順。"""
    global _last_bar_detection
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
            found.append((child, rect[0], rect[1], win32gui.GetParent(child)))
        except Exception:
            pass
        return True

    try:
        win32gui.EnumChildWindows(hwnd, cb, None)
    except Exception:
        pass
    if len(found) != 32:
        _last_bar_detection = f"⚠️ ボタンが32個見つかりません({len(found)}個)"
        return None, None

    by_parent = {}
    for item in found:
        by_parent.setdefault(item[3], []).append(item)

    def sorted_hwnds(items):
        items.sort(key=lambda item: (item[1], item[2]))
        return [item[0] for item in items]

    if len(by_parent) == 2 and all(len(v) == 16 for v in by_parent.values()):
        info = []
        for parent, items in by_parent.items():
            try:
                bar_id = win32api.GetWindowLong(parent, win32con.GWL_ID)
            except Exception:
                bar_id = None
            try:
                caption = win32gui.GetWindowText(parent)
            except Exception:
                caption = ""
            info.append((bar_id, caption, items))
        if all(i[0] is not None for i in info):
            info.sort(key=lambda i: i[0])
            layer_hwnds = sorted_hwnds(info[0][2])
            group_hwnds = sorted_hwnds(info[1][2])
            _last_bar_detection = (
                f"ツールバーID順で判別OK "
                f"(レイヤ=ID{info[0][0]}/表示{info[0][1]!r}、"
                f"レイヤグループ=ID{info[1][0]}/表示{info[1][1]!r})"
            )
            return layer_hwnds, group_hwnds

    # 👑 IDが読めない等の想定外環境でのみ、従来のx座標順の推定に戻す
    # (機能ごと死なせないため。ただし入れ替わる可能性があるので記録する)。
    _last_bar_detection = (
        "⚠️ ツールバーIDで判別できずx座標順の推定にフォールバック"
        f"(親の数={len(by_parent)}) — レイヤとレイヤグループが入れ替わる可能性があります"
    )
    found.sort(key=lambda item: (item[1], item[2]))
    return [item[0] for item in found[:16]], [item[0] for item in found[16:]]


_LAYER_LIST_DIALOG_TITLES = ("レイヤ一覧", "レイヤグループ一覧")


def _close_stray_layer_list_dialogs(stop_event):
    """👑 「既に選択中のボタンを右クリック」の誤判定(set_layer_group()の
    事前チェックが読み取りタイミングの問題で外れることがある、実機確認
    2026-09-11)を防ぎきれない場合の保険。「レイヤ一覧」「レイヤグループ
    一覧」ダイアログはモーダルで、開くと_right_click()内のSendMessageが
    そのダイアログが閉じるまで戻ってこない(WM_RBUTTONUP送信がブロック
    されたまま固まる)。このため、SendMessageと**並行して別スレッドで**
    ダイアログの出現を監視し、見つかり次第WM_CLOSEを送って閉じる
    (PostMessageは別スレッドからでも非同期に届くため、送信元スレッドが
    SendMessageでブロック中でも問題なく効く)。"""
    while not stop_event.is_set():
        def cb(h, _extra):
            try:
                if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "#32770":
                    title = win32gui.GetWindowText(h)
                    if any(t in title for t in _LAYER_LIST_DIALOG_TITLES):
                        win32gui.PostMessage(h, win32con.WM_CLOSE, 0, 0)
            except Exception:
                pass
            return True

        try:
            win32gui.EnumWindows(cb, None)
        except Exception:
            pass
        stop_event.wait(0.02)


def _right_click(target_hwnd, hwnd_for_foreground):
    force_foreground_window(hwnd_for_foreground)
    time.sleep(0.05)
    l, t, r, b = win32gui.GetWindowRect(target_hwnd)
    w_, h_ = r - l, b - t
    lparam = win32api.MAKELONG(w_ // 2, h_ // 2)

    stop_event = threading.Event()
    watchdog = threading.Thread(
        target=_close_stray_layer_list_dialogs, args=(stop_event,), daemon=True
    )
    watchdog.start()
    try:
        win32gui.SendMessage(target_hwnd, WM_RBUTTONDOWN, 0, lparam)
        time.sleep(0.05)
        win32gui.SendMessage(target_hwnd, WM_RBUTTONUP, 0, lparam)
        time.sleep(0.05)
    finally:
        stop_event.set()
        watchdog.join(timeout=1)


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
    if not found:
        # 👑 2026-09-16: ここが見つからないとread_current_layer_group()が
        # (None, None)を返す。すると set_layer_group() の「既に選択中の
        # ボタンは右クリックしない」という判定が効かなくなり、レイヤ一覧
        # ダイアログが勝手に開く(同関数の👑コメント参照)。実害があるのに
        # 今まで黙ってNoneを返していたので記録する。
        diagnostics.note(
            "jw_cadのステータスバー",
            "見つかりません(現在のレイヤ/グループを読めず、"
            "レイヤ一覧ダイアログが開く場合があります)",
        )
    else:
        diagnostics.ok("jw_cadのステータスバー")
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


def capture_swatches(hwnd, on_color=None, on_type=None, on_dialog_found=None):
    """線属性ダイアログを開いて色9個・線種9個の実際の見本を読み取り、
    変更せずキャンセルで閉じる。戻り値:
    {"colors": [(ctrl_id, "#rrggbb"), ...], "types": [(ctrl_id, [bool,...]), ...]}
    (読み取り失敗時はNone)。
    👑 on_color(ctrl_id, hex_color)/on_type(ctrl_id, pattern)を渡すと、
    1項目読み取るたびに都度呼ばれる(「読めたもの1個ずつ更新していけたら
    臨場感あるけどできそう？」への対応。呼び出し元がTkinterのメイン
    スレッドから同期的に呼ぶ前提で、別スレッド化はしていない)。
    👑 2026-09-15: on_dialog_found(rect)を渡すと、線属性ダイアログの
    実際の位置(win32gui.GetWindowRectのタプル)が分かった時点で1回だけ
    呼ばれる。GetPixelは画面の絶対座標を読むだけなので、呼び出し元の
    ウィンドウがこの矩形と重ならない位置へどければ、呼び出し元は
    topmostのままでも正しく読み取れる(「せっかく1個ずつ更新している
    のに、自分の窓が裏に回って見えないのは面白くない」というユーザー
    指摘への対応)。"""
    dlg = _open_dialog(hwnd)
    if not dlg:
        return None
    if on_dialog_found:
        try:
            on_dialog_found(win32gui.GetWindowRect(dlg))
        except Exception:
            pass
    ctrl_map = _build_ctrl_map(dlg)
    # 👑 2026-09-24: この関数が読むのは**既定モードの**線色9個・線種9個
    # (COLOR_CTRL_IDS/TYPE_CTRL_IDS)。図面が「SXF対応拡張線色・線種」に
    # なっているとこれらのIDが別物になり、色は全部灰色、線種は別の線種の
    # 絵を読んでしまう。一旦既定モードへ落として読み、読み終えたら元の
    # 状態へ戻す(最後はキャンセル相当で閉じるので図面には残らないが、
    # チェックが即時反映される作りだった場合の副作用を避けるため明示的に
    # 戻す)。
    sxf_before = read_sxf_mode(ctrl_map)
    if sxf_before:
        dlg, ctrl_map, mode_ok = _set_sxf_mode(dlg, ctrl_map, False)
        if not mode_ok:
            diagnostics.note(
                "線属性の見本読み取り",
                "SXF対応を外せなかったため、見本が正しく読めません",
            )
        elif on_dialog_found:
            # 👑 切替でダイアログが作り直され、位置も大きさも変わる
            # (SXFモードの方が縦に長い)。呼び出し元が「どく」ための
            # 矩形を新しいもので通知し直す。
            try:
                on_dialog_found(win32gui.GetWindowRect(dlg))
            except Exception:
                pass
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

    if sxf_before:
        dlg, ctrl_map, _ = _set_sxf_mode(dlg, ctrl_map, True)
    # 👑 2026-09-24: SXFモードのダイアログには**キャンセルが無い**ため、
    # 以前のCANCEL_CTRL_ID頼みの閉じ方では開いたまま残り、モーダルで
    # jw_cadが操作不能になっていた(kamo報告の不具合と同じ原因がここにも
    # あった。設定画面の「見本で選ぶ」経由でも起きる)。
    _close_after_read(dlg, ctrl_map)

    return {"colors": colors, "types": types}
# ===== ✂️ utils/line_attr_dialog.py END ✂️ =====
