# ===== ✂️ utils/menu_prefs.py START ✂️ =====
"""
パレット右クリックメニューの、項目ごとの表示ON/OFF設定。tkinter/win32に
依存しない純粋モジュール（utils/window_state.pyと同じ方針）。「⚙️ 編集」
だけは常に表示（ここでは管理しない＝消せない）。window_state.jsonとは
意味が違う設定なので混ぜず、別ファイルにする。
"""
import json
import os
import sys

ITEM_KEYS = ("remember_position", "close_this_side", "show_hidden", "reset_preset", "exit")

ITEM_LABELS = {
    "remember_position": "📌 終了時の配置を記憶する",
    "close_this_side": "このパレットだけを閉じる",
    "show_hidden": "👁️ 隠したパレットを再表示",
    "reset_preset": "🔄 初期構成を選び直す",
    "exit": "❌ JwNaviシステムを終了する",
}


def _resolve_base_dir():
    try:
        script_path_str, *_ = sys.argv
        exe_dir = os.path.dirname(os.path.abspath(script_path_str))
        if os.path.isdir(exe_dir):
            return exe_dir
    except Exception:
        pass
    return os.getcwd()


def prefs_path():
    path = os.path.join(_resolve_base_dir(), "config", "menu_prefs.json")
    if os.path.exists(path):
        return path
    return os.path.join("config", "menu_prefs.json")


def default_prefs():
    return {key: True for key in ITEM_KEYS}


def load_prefs():
    try:
        path = prefs_path()
        if not os.path.exists(path):
            return default_prefs()
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        prefs = default_prefs()
        for key in ITEM_KEYS:
            if key in raw:
                prefs[key] = bool(raw[key])
        return prefs
    except Exception:
        return default_prefs()


def save_prefs(prefs):
    path = prefs_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump({key: bool(prefs.get(key, True)) for key in ITEM_KEYS}, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
# ===== ✂️ utils/menu_prefs.py END ✂️ =====
