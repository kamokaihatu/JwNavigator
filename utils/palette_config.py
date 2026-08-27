# ===== ✂️ utils/palette_config.py START ✂️ =====
"""
パレット(左右ツールバー)のボタン配置をconfig/config.jsonとして読み書きする。
tkinter/win32に依存しない純粋モジュール（utils/palette_layout.pyと同じ方針）。
"""
import copy
import glob
import json
import os
import sys

SIDES = ("左", "右")
ORIENTATION_PORTRAIT = "portrait"
ORIENTATION_LANDSCAPE = "landscape"
ORIENTATIONS = (ORIENTATION_PORTRAIT, ORIENTATION_LANDSCAPE)
NO_ICON = ""
DEFAULT_BUTTON_SIZE = 48
MIN_BUTTON_SIZE = 32
MAX_BUTTON_SIZE = 96
DEFAULT_COLOR = "#f0f0f0"
# 👑 サブコマンド(command_kind=="サブ")は、jw_cad自身のボタン文字色が
# 紺/青である慣習に合わせ、追加時のデフォルト背景色を薄い青系にして
# 見分けやすくする（ユーザー要望）。追加後に個別に色変更するのは自由。
SUB_COMMAND_DEFAULT_COLOR = "#cfe0f5"
MAX_GROUP_LEN = 30
CONFIG_VERSION = 2

_COLOR_RE_LEN = 7  # "#RRGGBB"


def _resolve_base_dir():
    try:
        script_path_str, *_ = sys.argv
        exe_dir = os.path.dirname(os.path.abspath(script_path_str))
        if os.path.isdir(exe_dir):
            return exe_dir
    except Exception:
        pass
    return os.getcwd()


def config_path():
    path = os.path.join(_resolve_base_dir(), "config", "config.json")
    if os.path.exists(path):
        return path
    return os.path.join("config", "config.json")


def _icons_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")


def _png_icons_dir():
    return os.path.join(_resolve_base_dir(), "png_icons")


def list_icon_modules():
    try:
        paths = glob.glob(os.path.join(_icons_dir(), "*.py"))
    except Exception:
        return []
    names = []
    for p in paths:
        stem = os.path.splitext(os.path.basename(p))[0]
        if stem.startswith("__"):
            continue
        names.append(stem)
    return sorted(names)


def png_icon_path(name):
    return os.path.join(_png_icons_dir(), f"{name}.png")


def list_png_icons():
    try:
        paths = glob.glob(os.path.join(_png_icons_dir(), "*.png"))
    except Exception:
        return []
    return sorted(os.path.splitext(os.path.basename(p))[0] for p in paths)


def list_all_icon_names():
    # 👑 widgets/button.pyのload_and_draw()は、同名のpng_icons/*.pngが
    # あればそちらを.pyモジュールより優先して使う。アイコン選択UIでは
    # 両方の由来を区別せず、存在するアイコン名を一覧として扱う。
    return sorted(set(list_icon_modules()) | set(list_png_icons()))


def new_button(command_id, name, icon=NO_ICON, color=DEFAULT_COLOR):
    return {
        "command_id": command_id,
        "name": name,
        "icon": icon or NO_ICON,
        "color": color or DEFAULT_COLOR,
    }


def new_group(buttons=None):
    return {"buttons": list(buttons) if buttons else []}


def _default_side():
    return {
        "orientation": ORIENTATION_PORTRAIT,
        "button_size": DEFAULT_BUTTON_SIZE,
        "groups": [],
    }


def default_config():
    return {
        "version": CONFIG_VERSION,
        "sides": {side: _default_side() for side in SIDES},
    }


def _is_valid_color(value):
    if not isinstance(value, str) or len(value) != _COLOR_RE_LEN or value[0] != "#":
        return False
    try:
        int(value[1:], 16)
        return True
    except ValueError:
        return False


def _normalize_button(raw, known_icons):
    if not isinstance(raw, dict):
        return None
    command_id = str(raw.get("command_id") or "").strip()
    if not command_id:
        return None
    name = str(raw.get("name") or "").strip() or command_id
    icon = str(raw.get("icon") or "").strip()
    if icon and icon not in known_icons:
        icon = NO_ICON
    color = raw.get("color")
    if not _is_valid_color(color):
        color = DEFAULT_COLOR
    return {"command_id": command_id, "name": name, "icon": icon, "color": color}


def _normalize_group(raw, known_icons):
    if isinstance(raw, dict):
        raw_buttons = raw.get("buttons")
    elif isinstance(raw, list):
        raw_buttons = raw
    else:
        raw_buttons = None
    if not isinstance(raw_buttons, list):
        return None

    buttons = []
    for item in raw_buttons:
        btn = _normalize_button(item, known_icons)
        if btn:
            buttons.append(btn)
    if not buttons:
        return None

    groups = []
    for i in range(0, len(buttons), MAX_GROUP_LEN):
        groups.append({"buttons": buttons[i:i + MAX_GROUP_LEN]})
    return groups


def _normalize_side(raw, known_icons):
    if not isinstance(raw, dict):
        raw = {}

    orientation = raw.get("orientation")
    if orientation not in ORIENTATIONS:
        orientation = ORIENTATION_PORTRAIT

    try:
        button_size = int(raw.get("button_size", DEFAULT_BUTTON_SIZE))
    except (TypeError, ValueError):
        button_size = DEFAULT_BUTTON_SIZE
    button_size = max(MIN_BUTTON_SIZE, min(MAX_BUTTON_SIZE, button_size))

    raw_groups = raw.get("groups")
    groups = []
    if isinstance(raw_groups, list):
        for raw_group in raw_groups:
            normalized = _normalize_group(raw_group, known_icons)
            if normalized:
                groups.extend(normalized)

    return {"orientation": orientation, "button_size": button_size, "groups": groups}


def normalize_config(raw):
    if not isinstance(raw, dict):
        return default_config()

    known_icons = set(list_all_icon_names())

    try:
        version = int(raw.get("version", CONFIG_VERSION))
    except (TypeError, ValueError):
        version = CONFIG_VERSION

    raw_sides = raw.get("sides")
    if not isinstance(raw_sides, dict):
        raw_sides = {}

    sides = {}
    for side in SIDES:
        sides[side] = _normalize_side(raw_sides.get(side), known_icons)

    return {"version": version, "sides": sides}


def load_config():
    path = config_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return default_config()
    return normalize_config(raw)


def save_config(config):
    normalized = normalize_config(config)
    path = config_path()
    config_dir = os.path.dirname(path) or "."
    os.makedirs(config_dir, exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp_path, path)


def side_config(config, side):
    return config["sides"][side]


def clone_config(config):
    return copy.deepcopy(config)


def count_buttons(side_cfg):
    return sum(len(group.get("buttons", [])) for group in side_cfg.get("groups", []))
# ===== ✂️ utils/palette_config.py END ✂️ =====
