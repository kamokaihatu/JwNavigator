# ===== ✂️ utils/auto_attr_state.py START ✂️ =====
"""
線属性ボタン(kind="auto_attr")が「元に戻す前」の状態(original属性・
確認済みフラグ・切替先コマンド)を、JwNavigator自体の再起動をまたいで
覚えておくための読み書き。tkinter/win32に依存しない純粋モジュール
(utils/window_state.pyと同じ方針)。

👑 「補助線のまま再起動かかって、直線から始まったときに補助線属性に
なっちゃう」への対応。_auto_attr_pendingは元々main.pyのメモリ上だけに
あったため、JwNavigator側だけが再起動(開発中の頻繁な再起動、クラッシュ
等)されるとjw_cad自体は補助線色/線種のまま動き続けているのに、元に戻す
ための「original」を丸ごと失っていた。ここに保存しておき、起動時に
読み直すことでこの状況を回避する。jw_cad自体が別プロセスなので、
JwNavigatorが再起動してもjw_cad側の実際の線属性はそのまま(変化しない)
という前提で成り立つ。
"""
import json
import os
import sys


def _resolve_base_dir():
    try:
        script_path_str, *_ = sys.argv
        exe_dir = os.path.dirname(os.path.abspath(script_path_str))
        if os.path.isdir(exe_dir):
            return exe_dir
    except Exception:
        pass
    return os.getcwd()


def state_path():
    path = os.path.join(_resolve_base_dir(), "config", "auto_attr_pending.json")
    if os.path.exists(path):
        return path
    return os.path.join("config", "auto_attr_pending.json")


def load_pending():
    """戻り値: {hwnd(int): {"original":..., "confirmed":..., "target_command":...,
    "horizontal_vertical":...}}。読み取れなければ空dict。"""
    try:
        path = state_path()
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            return {}
        result = {}
        for hwnd_str, entry in raw.items():
            try:
                hwnd = int(hwnd_str)
            except (TypeError, ValueError):
                continue
            if isinstance(entry, dict) and isinstance(entry.get("original"), dict):
                result[hwnd] = entry
        return result
    except Exception:
        return {}


def save_pending(pending_by_hwnd):
    """pending_by_hwnd: main.pyのself._auto_attr_pending(hwnd(int)キー、値に
    trigger_btn等のtkinterウィジェットを含む)をそのまま渡してよい。
    ウィジェットはシリアライズできない/再起動後は無意味なので、ここで
    必要な項目だけ抜き出して保存する。"""
    try:
        path = state_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        serializable = {}
        for hwnd, entry in pending_by_hwnd.items():
            if not isinstance(entry, dict) or not isinstance(entry.get("original"), dict):
                continue
            serializable[str(hwnd)] = {
                "original": entry.get("original"),
                "confirmed": bool(entry.get("confirmed")),
                "target_command": entry.get("target_command"),
                "horizontal_vertical": bool(entry.get("horizontal_vertical")),
            }
        if not serializable:
            if os.path.exists(path):
                os.remove(path)
            return
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        pass
# ===== ✂️ utils/auto_attr_state.py END ✂️ =====
