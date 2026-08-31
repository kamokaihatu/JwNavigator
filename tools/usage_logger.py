# ===== ✂️ tools/usage_logger.py START ✂️ =====
"""
JwNavigator本体とは独立した、簡易利用状況ログ収集ツール。

「JwNavigatorを使っていない人にもログ収集だけ依頼したい」という
想定のため、本体(main.py)のGUI・フック等には一切依存しない。
小さなウィンドウを表示している間だけ記録し、「終了して保存」ボタン
（またはウィンドウを閉じる）で、それまでの集計をログファイルへ書き出す。

記録する内容（座標やキーの種類は記録しない）:
  - コマンドごとの使用回数（jw_cad自身のツールバーボタンの
    TBSTATE_CHECKEDビットを定期的に見て、「未選択→選択」に変わった
    瞬間を1回とカウントする）
  - コマンドごとの「実行中」の左クリック・右クリック・Escape回数
    （そのコマンドがCHECKED状態の間に起きたクリック/Escapeを、その
    コマンドの分としてカウントする。「この後すぐ戻るを押した回数」も
    同様に、直前にCHECKEDだったコマンドの分としてカウントする —
    「このコマンド、よく失敗してやり直してるな」が見える）
  - 左クリック回数・右クリック回数・キー入力回数・Escapeキー押下回数
    （全体合計。GetAsyncKeyStateによる安全なポーリング。WH_MOUSE_LL等の
    低レベルフックは、本体側で実機クラッシュが確認され意図的に
    使っていないため、ここでも使わない）
  - 戻る(Undo)・上書き保存・名前を付けて保存の使用回数（これらは
    選択状態が残らない単発コマンドのためCHECKEDビット方式では検出
    できない。また複数段階のUndo履歴を持つ戻るはTBSTATE_ENABLEDビット
    でも検出できないことが実測で判明した。代わりにjw_cad自身の
    ツールバーを物理的にクリックした瞬間だけ立つTBSTATE_PRESSEDビットを
    見る。ただしこれはJwNavigator経由の送信やCtrl+Z/Ctrl+S等の
    ショートカットでは立たないため、jw_cad自身のツールバーを直接
    クリックした場合のみのカウントである点に注意）

使い方:
    .venv\\Scripts\\python.exe tools\\usage_logger.py
    （または配布用exe: JwNavigator_UsageLogger.exe をダブルクリック）
"""
import os
import sys
import time
import datetime
import tkinter as tk
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import win32gui
import win32process
import win32api
import win32con

from utils import command_master
from utils.send_command import get_command_checked_states, get_command_pressed_states

JW_CAD_EXE_NAME = "jw_win.exe"
COMMAND_POLL_INTERVAL_SEC = 1.0
INPUT_POLL_INTERVAL_SEC = 150  # ms（tk root.after用。GetAsyncKeyStateポーリングと同じ間隔）
AUTOSAVE_INTERVAL_SEC = 10.0

# 👑 CHECKEDビットが立たない単発コマンド用に、PRESSEDビット（jw_cad自身の
# ツールバーを物理的にクリックした瞬間だけ立つ）で使用を検出するコマンド。
# 戻る(C028)は「直前に使っていたコマンドの分」として追加集計もする
# （UNDO_ATTRIBUTION_COMMAND_ID）。上書き保存(C041)・名前を付けて保存
# (C042)は単純に単発コマンドとしての合計回数だけ取る。
MOMENTARY_ESTIMATE_COMMAND_IDS = {"C028", "C041", "C042"}
UNDO_ATTRIBUTION_COMMAND_ID = "C028"

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
                         key_press_count, escape_press_count, momentary_estimated_counts,
                         during_left, during_right, during_escape, undo_after):
    lines = []
    lines.append(f"=== JwNavigator 簡易利用状況ログ ===")
    lines.append(f"開始: {started_at.isoformat(timespec='seconds')}")
    lines.append(f"終了: {ended_at.isoformat(timespec='seconds')}")
    lines.append(f"左クリック回数: {left_click_count}")
    lines.append(f"右クリック回数: {right_click_count}")
    lines.append(f"キー入力回数: {key_press_count}")
    lines.append(f"Escapeキー押下回数: {escape_press_count}")
    lines.append(
        "コマンド別使用回数（[]内はそのコマンドが選択されていた間に起きた"
        "左右クリック・Escape・その直後に戻るが押された回数）:"
    )
    used = [(cid, name, cnt) for cid, (name, _idc) in id_map.items() for cnt in [command_counts[cid]] if cnt > 0]
    used.sort(key=lambda x: -x[2])
    if used:
        for cid, name, cnt in used:
            lines.append(
                f"  {cid} {name}: {cnt}回"
                f" [左{during_left.get(cid, 0)} 右{during_right.get(cid, 0)}"
                f" Esc{during_escape.get(cid, 0)} 戻る{undo_after.get(cid, 0)}]"
            )
    else:
        lines.append("  (使用されたコマンドはありませんでした)")

    estimated = [(cid, id_map[cid][0], cnt) for cid, cnt in momentary_estimated_counts.items() if cnt > 0]
    if estimated:
        lines.append("単発コマンド使用回数（jw_cad自身のツールバーを直接クリックした場合のみ検出。"
                     "JwNavigator経由やCtrl+Z/Ctrl+S等のショートカットは含まれません）:")
        for cid, name, cnt in estimated:
            lines.append(f"  {cid} {name}: {cnt}回")
    return lines


class UsageLoggerApp:
    def __init__(self):
        self.id_map = {}
        for row in command_master.list_available_commands():
            if row.get("id_command"):
                self.id_map[row["command_id"]] = (row["toolbar_name"], row["id_command"])

        self.command_counts = {cid: 0 for cid in self.id_map}
        self.prev_checked = {}
        self.left_click_count = 0
        self.right_click_count = 0
        self.key_press_count = 0
        self.escape_press_count = 0

        self.prev_left_down = False
        self.prev_right_down = False
        self.prev_any_key_down = False
        self.prev_escape_down = False

        # 👑 「今まさにCHECKEDになっているコマンド」を覚えておき、その間に
        # 起きたクリック/Escape/直後の戻るを、そのコマンドの分として集計
        # する。全コマンドが非CHECKEDに戻ったらNoneに戻す（後述のtickで
        # 判定）。
        self.currently_checked_cid = None
        self.during_left = defaultdict(int)
        self.during_right = defaultdict(int)
        self.during_escape = defaultdict(int)
        self.undo_after = defaultdict(int)

        self.momentary_ids = {cid: idc for cid, (_, idc) in self.id_map.items() if cid in MOMENTARY_ESTIMATE_COMMAND_IDS}
        self.momentary_estimated_counts = {cid: 0 for cid in self.momentary_ids}
        self.prev_pressed = {}

        self.last_command_poll = 0.0
        self.last_autosave = time.time()
        self.cached_hwnd = None
        self.started_at = datetime.datetime.now()
        self._finalized = False

        self.root = tk.Tk()
        self.root.title("JwNavigator 利用状況ログ")
        self.root.geometry("360x210")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_stop_clicked)

        self.body_frame = tk.Frame(self.root)
        self.body_frame.pack(fill="both", expand=True)

        tk.Label(
            self.body_frame, text="計測中です。作業が終わったら\n下のボタンで終了・保存してください。",
            font=("Meiryo UI", 10), justify="center",
        ).pack(pady=(12, 6))
        tk.Label(
            self.body_frame, text="(コマンド使用回数・クリック回数・キー入力回数のみ記録。\n座標やキーの内容は記録しません)",
            font=("Meiryo UI", 8), fg="#666666", justify="center",
        ).pack()

        self.status_label = tk.Label(self.body_frame, font=("Meiryo UI", 9), justify="left", anchor="w")
        self.status_label.pack(fill="x", padx=16, pady=(10, 4))

        self.stop_button = tk.Button(
            self.body_frame, text="終了して保存", font=("Meiryo UI", 11, "bold"),
            command=self._on_stop_clicked, bg="#2b4c7e", fg="white", relief="raised",
        )
        self.stop_button.pack(pady=(6, 12))

        self._update_status_label()
        self.root.after(INPUT_POLL_INTERVAL_SEC, self._tick)

    def _update_status_label(self):
        elapsed = datetime.datetime.now() - self.started_at
        elapsed_str = str(elapsed).split(".")[0]
        total_commands = sum(self.command_counts.values()) + sum(self.momentary_estimated_counts.values())
        self.status_label.configure(
            text=(
                f"経過時間: {elapsed_str}\n"
                f"クリック: 左{self.left_click_count} 右{self.right_click_count}　"
                f"キー入力: {self.key_press_count}　Esc: {self.escape_press_count}\n"
                f"コマンド使用: 合計{total_commands}回"
            )
        )

    def _tick(self):
        if self._finalized:
            return
        now = time.time()

        if now - self.last_command_poll >= COMMAND_POLL_INTERVAL_SEC:
            self.last_command_poll = now
            self.cached_hwnd = find_jw_cad_hwnd()
            if self.cached_hwnd:
                id_commands = [idc for _, idc in self.id_map.values()]
                states = get_command_checked_states(self.cached_hwnd, id_commands)
                newly_checked = None
                any_checked_now = False
                for cid, (_, idc) in self.id_map.items():
                    checked = bool(states.get(idc))
                    if checked:
                        any_checked_now = True
                        if not self.prev_checked.get(idc, False):
                            self.command_counts[cid] += 1
                            newly_checked = cid
                    self.prev_checked[idc] = checked
                if newly_checked:
                    self.currently_checked_cid = newly_checked
                elif not any_checked_now:
                    self.currently_checked_cid = None

        # 👑 戻る等の単発コマンドはPRESSEDビットがマウスダウン中の一瞬しか
        # 立たないため、1秒間隔のコマンドポーリングでは取りこぼす。クリック
        # 検出と同じ間隔で見ることで、実際のクリックと同じ粒度で押下の
        # 立ち上がりを拾う（find_jw_cad_hwndの再列挙は重いので、直近の
        # 1秒ポーリングで見つけたhwndをそのまま使い回す）。
        if self.momentary_ids and self.cached_hwnd:
            pressed_states = get_command_pressed_states(self.cached_hwnd, list(self.momentary_ids.values()))
            for cid, idc in self.momentary_ids.items():
                pressed = pressed_states.get(idc)
                if pressed and not self.prev_pressed.get(idc, False):
                    self.momentary_estimated_counts[cid] += 1
                    if cid == UNDO_ATTRIBUTION_COMMAND_ID and self.currently_checked_cid:
                        self.undo_after[self.currently_checked_cid] += 1
                if pressed is not None:
                    self.prev_pressed[idc] = pressed

        left_down = bool(win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000)
        if left_down and not self.prev_left_down:
            self.left_click_count += 1
            if self.currently_checked_cid:
                self.during_left[self.currently_checked_cid] += 1
        self.prev_left_down = left_down

        right_down = bool(win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000)
        if right_down and not self.prev_right_down:
            self.right_click_count += 1
            if self.currently_checked_cid:
                self.during_right[self.currently_checked_cid] += 1
        self.prev_right_down = right_down

        any_key_down = _any_key_down()
        if any_key_down and not self.prev_any_key_down:
            self.key_press_count += 1
        self.prev_any_key_down = any_key_down

        escape_down = bool(win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000)
        if escape_down and not self.prev_escape_down:
            self.escape_press_count += 1
            if self.currently_checked_cid:
                self.during_escape[self.currently_checked_cid] += 1
        self.prev_escape_down = escape_down

        if now - self.last_autosave >= AUTOSAVE_INTERVAL_SEC:
            self.last_autosave = now
            self._autosave()

        self._update_status_label()
        self.root.after(INPUT_POLL_INTERVAL_SEC, self._tick)

    def _report_lines(self, ended_at):
        return _build_report_lines(
            self.started_at, ended_at, self.id_map, self.command_counts,
            self.left_click_count, self.right_click_count, self.key_press_count,
            self.escape_press_count, self.momentary_estimated_counts,
            self.during_left, self.during_right, self.during_escape, self.undo_after,
        )

    def _autosave(self):
        try:
            lines = self._report_lines(datetime.datetime.now())
            with open(_autosave_path(), "w", encoding="utf-8") as f:
                f.write("(自動保存・途中経過)\n" + "\n".join(lines) + "\n")
        except Exception:
            pass

    def _on_stop_clicked(self):
        if self._finalized:
            return
        self._finalized = True

        ended_at = datetime.datetime.now()
        lines = self._report_lines(ended_at)
        text = "\n".join(lines)

        path = _log_path()
        save_ok = True
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(text + "\n\n")
        except Exception:
            save_ok = False

        try:
            autosave_path = _autosave_path()
            if os.path.exists(autosave_path):
                os.remove(autosave_path)
        except Exception:
            pass

        self._show_done_screen(save_ok, path)

    def _show_done_screen(self, save_ok, path):
        # 👑 それまで無言でウィンドウが閉じるだけだったが、「本当に保存
        # されたのか」が同僚から見て分かりにくいという指摘を受け、保存
        # 結果を一言表示してから、ユーザー自身が閉じる操作に変更した。
        for child in self.body_frame.winfo_children():
            child.destroy()

        if save_ok:
            message = f"計測を終了し、保存しました。\n\n「{os.path.basename(path)}」\nというファイルをお送りください。"
        else:
            message = "計測は終了しましたが、\nログの保存に失敗しました。"

        tk.Label(
            self.body_frame, text=message, font=("Meiryo UI", 11),
            justify="center", wraplength=320,
        ).pack(pady=(30, 20), padx=16)
        tk.Button(
            self.body_frame, text="閉じる", font=("Meiryo UI", 11, "bold"),
            command=self.root.destroy, bg="#2b4c7e", fg="white", relief="raised",
        ).pack(pady=(0, 20))

    def run(self):
        self.root.mainloop()


def main():
    UsageLoggerApp().run()


if __name__ == "__main__":
    main()
# ===== ✂️ tools/usage_logger.py END ✂️ =====
