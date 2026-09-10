# ===== ✂️ utils/window_state.py START ✂️ =====
"""
パレットの「自由配置（ピン留め）」位置を終了時に記憶し、次回起動時に
復元するための読み書き。tkinter/win32に依存しない純粋モジュール
（utils/palette_config.pyと同じ方針）。config/config.json（ボタン配置）
とは別ファイルにして、意味の異なる設定を混ぜない。
"""
import json
import os

from utils.palette_config import SIDES
from utils import app_paths


def state_path():
    # 👑 2026-09-11: palette_config.config_path()と同じ理由で
    # utils/app_paths.pyのuser_config_dir()を使う(DECISIONS.md参照)。
    return os.path.join(app_paths.user_config_dir(), "window_state.json")


def default_state():
    state = {"remember_on_exit": False}
    for side in SIDES:
        state[side] = None
    return state


def load_state():
    try:
        path = state_path()
        if not os.path.exists(path):
            return default_state()
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        state = default_state()
        state["remember_on_exit"] = bool(raw.get("remember_on_exit", False))
        for side in SIDES:
            pos = raw.get(side)
            if (
                isinstance(pos, dict)
                and isinstance(pos.get("x"), int)
                and isinstance(pos.get("y"), int)
            ):
                state[side] = {"x": pos["x"], "y": pos["y"]}
        return state
    except Exception:
        return default_state()


def save_state(state):
    path = state_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def is_on_screen(x, y, w, h, virtual_screen):
    # 👑 保存された位置がモニター構成の変更等で画面外に出ていた場合、
    # 「二度と手の届かない場所に固定される」事故を防ぐため、復元前に
    # 必ず検証する（ユーザーからの明示的な懸念指摘を受けて追加）。
    v_left, v_top, v_width, v_height = virtual_screen
    return (
        x + w > v_left
        and x < v_left + v_width
        and y + h > v_top
        and y < v_top + v_height
    )
# ===== ✂️ utils/window_state.py END ✂️ =====
