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

# 👑 グループボタン（フライアウト/マクロ）の種別。「groups」（config.json内の
# 30個区切りのページング単位）とは無関係の別概念なので、変数名は
# button "kind" に統一し、混同しないようにする。
BUTTON_KIND_SINGLE = "single"
BUTTON_KIND_FLYOUT = "flyout"
BUTTON_KIND_MACRO = "macro"
BUTTON_KINDS_GROUP = (BUTTON_KIND_FLYOUT, BUTTON_KIND_MACRO)

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
    # 👑 PyInstaller等でexe化すると icons/*.py はディスク上のファイルとして
    # 存在しなくなる（--collect-submodulesでexe内に固められる）ため、
    # globベースの列挙はexe化後は常に空を返す。当初pkgutil.iter_modules()
    # で対応しようとしたが、凍結パッケージの__path__はPyInstaller内部の
    # 仮想パスで実ファイルが存在せず、常に空を返すことが実測で判明
    # （2026-08-31）。代わりにJwNavigator.spec側でicons/をdatasとしても
    # 実体コピーしており、sys._MEIPASS配下から通常のglobで列挙できる。
    if getattr(sys, "frozen", False):
        try:
            base = getattr(sys, "_MEIPASS", _resolve_base_dir())
            paths = glob.glob(os.path.join(base, "icons", "*.py"))
            return sorted(
                os.path.splitext(os.path.basename(p))[0] for p in paths
                if not os.path.basename(p).startswith("__")
            )
        except Exception:
            return []
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
        "kind": BUTTON_KIND_SINGLE,
    }


def new_group_button(name, kind, sub_buttons, icon=NO_ICON, color=DEFAULT_COLOR):
    # 👑 sub_buttonsは通常ボタンと同じ形のdictのリスト（ネストは1階層のみ、
    # sub_buttons自身がさらにkind=flyout/macroを持つことは許さない。
    # _normalize_button()側でallow_group=Falseとして弾く）。
    return {
        "command_id": "",
        "name": name,
        "icon": icon or NO_ICON,
        "color": color or DEFAULT_COLOR,
        "kind": kind,
        "sub_buttons": list(sub_buttons),
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


def _normalize_button(raw, known_icons, allow_group=True):
    if not isinstance(raw, dict):
        return None

    kind = raw.get("kind") if allow_group else BUTTON_KIND_SINGLE
    if kind not in BUTTON_KINDS_GROUP:
        kind = BUTTON_KIND_SINGLE

    name_fallback = ""
    if kind == BUTTON_KIND_SINGLE:
        command_id = str(raw.get("command_id") or "").strip()
        if not command_id:
            return None
        name_fallback = command_id
    else:
        # 👑 グループボタン自体はどのjw_cadコマンドにも対応しないので
        # command_idは持たない（クリック時はsub_buttonsの中身を実行する）。
        command_id = ""

    name = str(raw.get("name") or "").strip() or name_fallback or "グループ"
    icon = str(raw.get("icon") or "").strip()
    if icon and icon not in known_icons:
        icon = NO_ICON
    color = raw.get("color")
    if not _is_valid_color(color):
        color = DEFAULT_COLOR

    button = {"command_id": command_id, "name": name, "icon": icon, "color": color, "kind": kind}

    if kind != BUTTON_KIND_SINGLE:
        raw_sub = raw.get("sub_buttons")
        sub_buttons = []
        if isinstance(raw_sub, list):
            for item in raw_sub:
                # allow_group=False: sub_buttons自身はネストして
                # さらにグループを持てない（1階層のみ）。
                sub = _normalize_button(item, known_icons, allow_group=False)
                if sub:
                    sub_buttons.append(sub)
        # 👑 「先に空の箱を作って、あとから中身を詰める」使い方のため、
        # sub_buttonsが空でもグループボタン自体は保持する(以前はここで
        # Noneを返して丸ごと消していたため、空の箱がconfig.json保存の
        # たびに消滅していた)。
        button["sub_buttons"] = sub_buttons

    return button


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
