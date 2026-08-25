# ===== ✂️ utils/send_command.py START ✂️ =====
import time

import win32con
import win32gui
import win32api

from utils.send_key import force_foreground_window

WM_COMMAND = 0x0111
TB_GETSTATE = 0x0412
TBSTATE_ENABLED = 0x04


def _find_toolbar_windows(hwnd):
    # jw_cadは（ユーザーツールバーのページ違いなどで）同じidCommandを持つ
    # ToolbarWindow32を複数保持しており、非表示のものは古い/無関係な状態を
    # 返すことがある。実際に画面に出ている（IsWindowVisible）ものだけを
    # 対象にしないと、誤った有効/無効判定を拾ってしまう。
    toolbars = []

    def _cb(child, _extra):
        try:
            if win32gui.GetClassName(child) == "ToolbarWindow32" and win32gui.IsWindowVisible(child):
                toolbars.append(child)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumChildWindows(hwnd, _cb, None)
    except Exception:
        pass
    return toolbars


def _is_not_found_state(raw):
    # TB_GETSTATEは「idCommandが見つからない」場合-1を返すが、pywin32からは
    # 符号なし32bit（4294967295）で返ってくることがあるため両方を弾く。
    return raw is None or raw in (-1, 0xFFFFFFFF)


def is_command_enabled(hwnd: int, id_command: int):
    # jw_cad内の実際のツールバーボタンからidCommandの有効/無効状態を調べる。
    # 戻り値: True=有効, False=無効（グレーアウト）, None=どのツールバーにも
    # 見つからず判定不能（この場合は呼び出し側で「送信して構わない」扱いにする）。
    if not hwnd or not id_command:
        return None
    for tb_hwnd in _find_toolbar_windows(hwnd):
        try:
            state = win32gui.SendMessage(tb_hwnd, TB_GETSTATE, id_command, 0)
        except Exception:
            continue
        if _is_not_found_state(state):
            continue
        return bool(state & TBSTATE_ENABLED)
    return None


def get_command_states(hwnd: int, id_commands):
    # 複数のidCommandをまとめて調べる版。ツールバー列挙を1回だけで済ませる。
    # 戻り値: {id_command: True/False/None}
    result = {}
    if not hwnd:
        return {i: None for i in id_commands}
    toolbars = _find_toolbar_windows(hwnd)
    for id_command in id_commands:
        state = None
        for tb_hwnd in toolbars:
            try:
                raw = win32gui.SendMessage(tb_hwnd, TB_GETSTATE, id_command, 0)
            except Exception:
                continue
            if _is_not_found_state(raw):
                continue
            state = bool(raw & TBSTATE_ENABLED)
            break
        result[id_command] = state
    return result


def send_command_to_hwnd(hwnd: int, id_command: int) -> bool:
    if not hwnd or not id_command:
        return False

    if not win32gui.IsWindowEnabled(hwnd):
        return False

    force_foreground_window(hwnd)
    time.sleep(0.015)

    if not win32gui.IsWindowEnabled(hwnd):
        return False

    wparam = win32api.MAKELONG(id_command, 0)
    win32gui.PostMessage(hwnd, WM_COMMAND, wparam, 0)
    return True
# ===== ✂️ utils/send_command.py END ✂️ =====
