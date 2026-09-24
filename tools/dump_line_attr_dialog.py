"""線属性ダイアログの中身を丸ごと書き出す調査用スクリプト。

👑 2026-09-24: 外部から受け取った図面が「SXF対応拡張線色・線種」に
なっていると、線色/線種のコントロールIDが総入れ替えになり、補助線
モードボタンが黙って何もせずに成功を返す不具合が出た。対応表を作る
ために、実機のダイアログを一度そのまま観測する。

使い方: jw_cadを起動し、対象の図面を開いた状態で
    .venv/Scripts/python.exe tools/dump_line_attr_dialog.py
ダイアログは最後にキャンセルで閉じるので、図面は変更されない。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import win32con
import win32gui

from utils import line_attr_dialog as lad

BM_GETCHECK = 0x00F0
BM_GETSTATE = 0x00F2


def _find_jw_cad():
    """👑 main.pyのfind_all_jw_cad_windows()と同じ判定(exe名で厳密一致)。
    クラス名やタイトルの部分一致は誤検出するので使わない。"""
    import win32process
    import win32api
    found = []

    def cb(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            if win32gui.GetParent(hwnd) != 0:
                return True
            if not win32gui.GetWindowText(hwnd):
                return True
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            h = win32api.OpenProcess(0x0400 | 0x0010, False, pid)
            try:
                path = win32process.GetModuleFileNameEx(h, 0)
            finally:
                win32api.CloseHandle(h)
            if os.path.basename(path).lower() == "jw_win.exe":
                found.append(hwnd)
        except Exception:
            pass
        return True

    win32gui.EnumWindows(cb, None)
    return found[0] if found else None


def main():
    hwnd = _find_jw_cad()
    if not hwnd:
        print("jw_cadのウィンドウが見つかりません。起動してから実行してください。")
        return 1
    print(f"jw_cad HWND={hwnd} title={win32gui.GetWindowText(hwnd)!r}")

    dlg = lad._open_dialog(hwnd)
    if not dlg:
        print("線属性ダイアログが開きませんでした。")
        return 1
    print(f"ダイアログ HWND={dlg} title={win32gui.GetWindowText(dlg)!r}")

    rows = []

    def cb(child, _):
        try:
            cid = win32gui.GetDlgCtrlID(child)
            cls = win32gui.GetClassName(child)
            text = win32gui.GetWindowText(child)
            l, t, r, b = win32gui.GetWindowRect(child)
            check = state = ""
            if cls.lower() == "button":
                try:
                    check = win32gui.SendMessage(child, BM_GETCHECK, 0, 0)
                    state = win32gui.SendMessage(child, BM_GETSTATE, 0, 0)
                except Exception:
                    pass
            style = win32gui.GetWindowLong(child, win32con.GWL_STYLE)
            rows.append((cid, cls, text, (l, t, r - l, b - t), check, state, style & 0xFF))
        except Exception:
            pass
        return True

    win32gui.EnumChildWindows(dlg, cb, None)
    rows.sort(key=lambda r: (r[3][1], r[3][0]))

    # 👑 コンソールの文字コードで日本語が化けるため、UTF-8のファイルにも
    # 同じ内容を書き出す(ラベルを正確に採るのが目的)。
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "line_attr_dump.txt")
    sep, nl = chr(9), chr(10)
    with io.open(out, "w", encoding="utf-8") as f:
        f.write(f"jw_cad title={win32gui.GetWindowText(hwnd)!r}" + nl)
        f.write(f"dialog hwnd={dlg}" + nl)
        f.write(f"controls={len(rows)}" + nl)
        for cid, cls, text, rect, check, state, bstyle in rows:
            rect_s = f"{rect[0]},{rect[1]},{rect[2]}x{rect[3]}"
            f.write(sep.join([str(cid), cls, rect_s, f"chk={check}",
                              f"state={state}", text]) + nl)
    print(f"[dump] {out} に書き出しました")

    print(f"\nコントロール {len(rows)} 個 (画面の上から順):")
    print(f"{'ctrl_id':>8} {'class':<14} {'x,y,w,h':<22} {'chk':>3} {'state':>5} {'btnstyle':>8}  text")
    for cid, cls, text, rect, check, state, bstyle in rows:
        rect_s = f"{rect[0]},{rect[1]},{rect[2]}x{rect[3]}"
        print(f"{cid:>8} {cls:<14} {rect_s:<22} {str(check):>3} {str(state):>5} {bstyle:>8}  {text!r}")

    # 👑 SXFモードのダイアログには「キャンセル」(ctrl_id=2)が無い。
    # 見つからない場合はWM_CLOSEで閉じる(OKを押すと今の表示内容を
    # 適用してしまうため、読み取りだけの時はWM_CLOSEを使う)。
    ctrl_map = lad._build_ctrl_map(dlg)
    if lad.CANCEL_CTRL_ID in ctrl_map:
        win32gui.SendMessage(ctrl_map[lad.CANCEL_CTRL_ID], 0x00F5, 0, 0)
        print("[close] キャンセルボタンで閉じました(図面は変更していません)。")
    else:
        win32gui.PostMessage(dlg, win32con.WM_CLOSE, 0, 0)
        print("[close] キャンセルボタンが無いのでWM_CLOSEで閉じました"
              "(SXFモードのダイアログにはキャンセルがありません)。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
