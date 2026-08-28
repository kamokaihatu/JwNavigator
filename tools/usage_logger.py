# ===== ✂️ tools/usage_logger.py START ✂️ =====
"""
JwNavigator本体とは独立した、簡易利用状況ログ収集ツール。

「JwNavigatorを使っていない人にもログ収集だけ依頼したい」という
想定のため、本体(main.py)のGUI・フック等には一切依存しない。
このスクリプトを単体で起動している間だけ記録し、Ctrl+Cで終了すると
それまでの集計をログファイルへ書き出す。

記録する内容（座標やキーの種類は記録しない）:
  - コマンドごとの使用回数（jw_cad自身のツールバーボタンの
    TBSTATE_CHECKEDビットを定期的に見て、「未選択→選択」に変わった
    瞬間を1回とカウントする。今日の開発で確立したCHECKEDビット方式を
    そのまま再利用している）
  - 左クリック回数・右クリック回数（GetAsyncKeyStateによる安全な
    ポーリング。WH_MOUSE_LL等の低レベルフックは、本体側で実機クラッシュ
    が確認され意図的に使っていないため、ここでも使わない）
  - キー入力回数（同様にポーリングで検出。どのキーかは記録しない）
  - Escapeキー押下回数（ESCは操作の取消しを表すだけで文字内容を含まない
    ため、他のキーとは別に単独でカウントしても構わないと判断した）
  - 戻る(Undo)の使用回数（「戻る」ボタンは選択状態が残らない単発
    コマンドのためCHECKEDビット方式では検出できない。また複数段階の
    Undo履歴を持つためTBSTATE_ENABLEDビット（有効/無効）の変化では
    履歴を使い切った時しか検出できないことが実測で判明した。代わりに
    jw_cad自身のツールバーを物理的にクリックした瞬間だけ立つ
    TBSTATE_PRESSEDビットを見る。ただしこれはJwNavigator経由の送信
    （WM_COMMANDを直接送るだけ）やCtrl+Z等のショートカットでは
    立たないため、jw_cad自身のツールバーを直接クリックした場合のみの
    カウントである点に注意）

使い方:
    .venv\\Scripts\\python.exe tools\\usage_logger.py
"""
import os
import sys
import time
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import win32gui
import win32process
import win32api
import win32con

from utils import command_master
from utils.send_command import get_command_checked_states, get_command_pressed_states

JW_CAD_EXE_NAME = "jw_win.exe"
COMMAND_POLL_INTERVAL_SEC = 1.0
INPUT_POLL_INTERVAL_SEC = 0.15
AUTOSAVE_INTERVAL_SEC = 10.0

# 👑 CHECKEDビットが立たない単発コマンド用に、PRESSEDビット（jw_cad自身の
# ツールバーを物理的にクリックした瞬間だけ立つ）で使用を検出するコマンド
# （今のところ戻るのみ）。JwNavigator経由やCtrl+Z等では検出できない点に
# 注意（PRESSEDは実際のマウスダウンでしか立たない）。
MOMENTARY_ESTIMATE_COMMAND_IDS = {"C028"}

# 👑 一般的なキー入力を広く検知するための走査範囲。VK_LBUTTON/VK_RBUTTON
# はクリックとして別カウントするのでここでは除外する。
_KEY_SCAN_CODES = [c for c in range(0x08, 0xFF) if c not in (win32con.VK_LBUTTON, win32con.VK_RBUTTON)]


def _get_exe_name(hwnd):
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        h = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid
        )
        path = win32process.GetModuleFileNameEx(h, 0)
        win32api.CloseHandle(h)
        return os.path.basename(path).lower()
    except Exception:
        return None


def find_jw_cad_hwnd():
    found = []

    def _cb(hwnd, _extra):
        try:
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetParent(hwnd) == 0:
                if _get_exe_name(hwnd) == JW_CAD_EXE_NAME:
                    found.append(hwnd)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumWindows(_cb, None)
    except Exception:
        pass
    return found[0] if found else None


def _log_path():
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv and sys.argv[0] else os.getcwd()
    return os.path.join(exe_dir, "JwNavigator_UsageLog.txt")


def _autosave_path():
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv and sys.argv[0] else os.getcwd()
    return os.path.join(exe_dir, "JwNavigator_UsageLog_進行中.txt")


def _any_key_down():
    for code in _KEY_SCAN_CODES:
        if win32api.GetAsyncKeyState(code) & 0x8000:
            return True
    return False


def _build_report_lines(started_at, ended_at, id_map, command_counts, left_click_count, right_click_count,
                         key_press_count, escape_press_count, momentary_estimated_counts):
    lines = []
    lines.append(f"=== JwNavigator 簡易利用状況ログ ===")
    lines.append(f"開始: {started_at.isoformat(timespec='seconds')}")
    lines.append(f"終了: {ended_at.isoformat(timespec='seconds')}")
    lines.append(f"左クリック回数: {left_click_count}")
    lines.append(f"右クリック回数: {right_click_count}")
    lines.append(f"キー入力回数: {key_press_count}")
    lines.append(f"Escapeキー押下回数: {escape_press_count}")
    lines.append("コマンド別使用回数:")
    used = [(cid, name, cnt) for cid, (name, _idc) in id_map.items() for cnt in [command_counts[cid]] if cnt > 0]
    used.sort(key=lambda x: -x[2])
    if used:
        for cid, name, cnt in used:
            lines.append(f"  {cid} {name}: {cnt}回")
    else:
        lines.append("  (使用されたコマンドはありませんでした)")

    estimated = [(cid, id_map[cid][0], cnt) for cid, cnt in momentary_estimated_counts.items() if cnt > 0]
    if estimated:
        lines.append("単発コマンド使用回数（jw_cad自身のツールバーを直接クリックした場合のみ検出。"
                     "JwNavigator経由やCtrl+Z等のショートカットは含まれません）:")
        for cid, name, cnt in estimated:
            lines.append(f"  {cid} {name}: {cnt}回")
    return lines


def main():
    id_map = {}
    for row in command_master.list_available_commands():
        if row.get("id_command"):
            id_map[row["command_id"]] = (row["toolbar_name"], row["id_command"])

    command_counts = {cid: 0 for cid in id_map}
    prev_checked = {}
    left_click_count = 0
    right_click_count = 0
    key_press_count = 0
    escape_press_count = 0

    prev_left_down = False
    prev_right_down = False
    prev_any_key_down = False
    prev_escape_down = False

    momentary_ids = {cid: idc for cid, (_, idc) in id_map.items() if cid in MOMENTARY_ESTIMATE_COMMAND_IDS}
    momentary_estimated_counts = {cid: 0 for cid in momentary_ids}
    prev_pressed = {}

    started_at = datetime.datetime.now()
    print("簡易ログ収集を開始しました。終了するにはCtrl+Cを押してください。")
    print("(コマンド使用回数・左右クリック回数・キー入力回数のみを記録し、座標やキーの種類は記録しません)")
    print(f"(異常終了に備え、{int(AUTOSAVE_INTERVAL_SEC)}秒ごとに途中経過を自動保存します: {_autosave_path()})")

    def _autosave():
        try:
            lines = _build_report_lines(
                started_at, datetime.datetime.now(), id_map, command_counts,
                left_click_count, right_click_count, key_press_count,
                escape_press_count, momentary_estimated_counts,
            )
            with open(_autosave_path(), "w", encoding="utf-8") as f:
                f.write("(自動保存・途中経過)\n" + "\n".join(lines) + "\n")
        except Exception:
            pass

    last_command_poll = 0.0
    last_autosave = time.time()
    cached_hwnd = None
    try:
        while True:
            now = time.time()

            if now - last_command_poll >= COMMAND_POLL_INTERVAL_SEC:
                last_command_poll = now
                cached_hwnd = find_jw_cad_hwnd()
                if cached_hwnd:
                    id_commands = [idc for _, idc in id_map.values()]
                    states = get_command_checked_states(cached_hwnd, id_commands)
                    for cid, (_, idc) in id_map.items():
                        checked = bool(states.get(idc))
                        if checked and not prev_checked.get(idc, False):
                            command_counts[cid] += 1
                        prev_checked[idc] = checked

            # 👑 戻る等の単発コマンドはPRESSEDビットがマウスダウン中の一瞬しか
            # 立たないため、1秒間隔のコマンドポーリングでは取りこぼす。クリック
            # 検出と同じ0.15秒刻みで見ることで、実際のクリックと同じ粒度で
            # 押下の立ち上がりを拾う（find_jw_cad_hwndの再列挙は重いので、
            # 直近の1秒ポーリングで見つけたhwndをそのまま使い回す）。
            if momentary_ids and cached_hwnd:
                pressed_states = get_command_pressed_states(cached_hwnd, list(momentary_ids.values()))
                for cid, idc in momentary_ids.items():
                    pressed = pressed_states.get(idc)
                    if pressed and not prev_pressed.get(idc, False):
                        momentary_estimated_counts[cid] += 1
                    if pressed is not None:
                        prev_pressed[idc] = pressed

            left_down = bool(win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000)
            if left_down and not prev_left_down:
                left_click_count += 1
            prev_left_down = left_down

            right_down = bool(win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000)
            if right_down and not prev_right_down:
                right_click_count += 1
            prev_right_down = right_down

            any_key_down = _any_key_down()
            if any_key_down and not prev_any_key_down:
                key_press_count += 1
            prev_any_key_down = any_key_down

            escape_down = bool(win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000)
            if escape_down and not prev_escape_down:
                escape_press_count += 1
            prev_escape_down = escape_down

            if now - last_autosave >= AUTOSAVE_INTERVAL_SEC:
                last_autosave = now
                _autosave()

            time.sleep(INPUT_POLL_INTERVAL_SEC)
    except KeyboardInterrupt:
        pass
    finally:
        ended_at = datetime.datetime.now()
        lines = _build_report_lines(
            started_at, ended_at, id_map, command_counts,
            left_click_count, right_click_count, key_press_count,
            escape_press_count, momentary_estimated_counts,
        )
        text = "\n".join(lines)
        print()
        print(text)

        path = _log_path()
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(text + "\n\n")
            print(f"\nログを保存しました: {path}")
        except Exception as e:
            print(f"\nログの保存に失敗しました: {e}")

        try:
            autosave_path = _autosave_path()
            if os.path.exists(autosave_path):
                os.remove(autosave_path)
        except Exception:
            pass


if __name__ == "__main__":
    main()
# ===== ✂️ tools/usage_logger.py END ✂️ =====
