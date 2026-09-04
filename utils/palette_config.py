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
import uuid

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

# 👑 「補助線」「配線」等、押すと線属性を自動で切り替えて直線コマンドへ
# 移動し、他コマンドに切り替わったら自動で元の線属性に戻すボタン。
# sub_buttonsを持たない点でBUTTON_KINDS_GROUPとは別枠(中身を持つ「箱」
# ではなく、単発の設定型ボタン)。doc/補助線ボタン_要件書.md参照。
BUTTON_KIND_AUTO_ATTR = "auto_attr"

# 👑 「電灯配線図」のようなレイヤ状態の保存/復元ボタン。押すたびに
# 「未保存→保存(Jw_cadのレイヤ設定を1回分記録)→以後は押すたびに復元」
# と切り替わる。実体はボタンごとに専用の.JWLファイル(config/layer_
# snapshots/<snapshot_id>.jwl)を持つだけで、状態(保存済みか)は
# そのファイルの有無で判定する(config.json側にフラグを二重管理しない)。
# doc/シート管理_設計メモ.md参照。
BUTTON_KIND_LAYER_SNAPSHOT = "layer_snapshot"

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


# 👑 線色1〜8+補助線色(9)、線種(実線〜二点鎖2)+補助線種(9)の、jw_cad
# 「線属性」ダイアログ上のctrl_id。utils/line_attr_dialog.py（win32依存）
# と同じ値をここにも持つ（このファイルはtkinter/win32非依存の方針の
# ため、あちらをimportしない。小さな定数の重複はwindow_state.py等の
# 既存パターンに合わせた許容範囲）。
LINE_COLOR_CTRL_IDS = (1401, 1402, 1403, 1404, 1405, 1406, 1407, 1408, 1409)
LINE_TYPE_CTRL_IDS = (2449, 2450, 2451, 2452, 2453, 2454, 2455, 2456, 2457)
LINE_COLOR_LABELS = ["線色1", "線色2", "線色3", "線色4", "線色5", "線色6", "線色7", "線色8", "補助線色"]
LINE_TYPE_LABELS = ["実線", "点線1", "点線2", "点線3", "一点鎖1", "一点鎖2", "二点鎖1", "二点鎖2", "補助線種"]
DEFAULT_LINE_COLOR_CTRL_ID = 1409  # 補助線色
DEFAULT_LINE_TYPE_CTRL_ID = 2457   # 補助線種

# 👑 レイヤ/レイヤグループ番号(0〜15)の表示ラベル(16進1桁、jw_cadの
# 表記に合わせて0〜9,A〜F)。「変更しない」を含めて設定画面のドロップ
# ダウンに使う。
LAYER_NUMBER_LABELS = ["変更しない"] + [f"{i:X}" for i in range(16)]

DEFAULT_AUTO_ATTR_TARGET_COMMAND = "C001"  # 直線

# 👑 補助線系ボタンの「対象」候補として画面に出す、実際に描画する系の
# コマンドだけの一覧(jw_cad本体の「作図」メニューと同じ構成、実機の
# メニュー総ざらいで確認済み)。「メイン」種別(39個)には戻る/進む/測定/
# 表計算/属性取得/建具平面(ファイル選択ダイアログを開く)等、描画モードに
# 入るわけではないコマンドも混ざっているため、それらをここで除外する。
# 👑 これはUIの選択候補を絞るための一覧であって、データ側
# (_normalize_button)はこのリスト外のtarget_commandも引き続き受け付ける
# (直接JSON編集等での利用を塞がない。ユーザー方針:「実は使えるみたいに
# しとかないと、使いたいときに改修が必要になるもんね」)。
AUTO_ATTR_DRAW_TARGET_COMMAND_IDS = (
    "C001",  # 線
    "C002",  # 矩形
    "C003",  # 円弧
    "C004",  # 文字
    "C005",  # 寸法
    "C006",  # 2線
    "C007",  # 中心線
    "C008",  # 連続線
    "C009",  # AUTO
    "C010",  # 点
    "C011",  # 接線
    "C012",  # 接円
    "C013",  # ハッチ
    "C017",  # 多角形
    "C019",  # 曲線
)


def new_auto_attr_button(
    name, line_color=DEFAULT_LINE_COLOR_CTRL_ID, line_type=DEFAULT_LINE_TYPE_CTRL_ID,
    line_width="", horizontal_vertical=False, layer_group=None, layer_number=None,
    target_command=DEFAULT_AUTO_ATTR_TARGET_COMMAND, icon=NO_ICON, color=DEFAULT_COLOR,
):
    # 👑 「補助線」「配線」等、押すと線属性を自動で切り替えて指定コマンド
    # へ移動し、他コマンドに切り替わったら自動で元の線属性に戻すボタン。
    # horizontal_vertical: 直線コマンドの「水平･垂直」条件も自動でONに
    # するか(ユーザー要望: 補助線は水平垂直をONにしたい)。
    # layer_group/layer_number: 0〜15(Noneなら変更しない)。押した時に
    # このレイヤグループ/レイヤへ自動で切り替え、離脱時に元へ戻す
    # (ユーザー要望: 「レイヤをF-Fへ変更してほしい」)。
    # target_command: 切替先コマンド(既定は直線=C001)。「連続線とか他の
    # コマンドも選べる？」というユーザー要望に対応。
    return {
        "command_id": "",
        "name": name,
        "icon": icon or NO_ICON,
        "color": color or DEFAULT_COLOR,
        "kind": BUTTON_KIND_AUTO_ATTR,
        "line_color": line_color,
        "line_type": line_type,
        "line_width": line_width or "",
        "horizontal_vertical": bool(horizontal_vertical),
        "layer_group": layer_group,
        "layer_number": layer_number,
        "target_command": target_command or DEFAULT_AUTO_ATTR_TARGET_COMMAND,
    }


def layer_snapshots_dir():
    d = os.path.join(os.path.dirname(config_path()), "layer_snapshots")
    os.makedirs(d, exist_ok=True)
    return d


def layer_snapshot_path(snapshot_id):
    return os.path.join(layer_snapshots_dir(), f"{snapshot_id}.jwl")


LAYER_SNAPSHOT_ROLE_SAVE = "save"
LAYER_SNAPSHOT_ROLE_RESTORE = "restore"
LAYER_SNAPSHOT_ROLES = (LAYER_SNAPSHOT_ROLE_SAVE, LAYER_SNAPSHOT_ROLE_RESTORE)


def new_layer_snapshot_button(name, role, snapshot_id=None, icon=NO_ICON, color=DEFAULT_COLOR):
    # 👑 snapshot_id省略時はここでuuidを自動生成する(ボタン名は後から
    # 変更されうるため、ファイル名には使わない)。
    # 👑 「右クリック=保存」は直感的でないというユーザー判断(2026-09-04)
    # により、保存用・復元用を別々のボタン(role)に分けた。同じ
    # snapshot_idを共有する2個のボタンを設定画面がペアで作る想定
    # (widgets/settings_window.py: _on_add_layer_snapshot)。
    if role not in LAYER_SNAPSHOT_ROLES:
        role = LAYER_SNAPSHOT_ROLE_RESTORE
    return {
        "command_id": "",
        "name": name,
        "icon": icon or NO_ICON,
        "color": color or DEFAULT_COLOR,
        "kind": BUTTON_KIND_LAYER_SNAPSHOT,
        "snapshot_id": snapshot_id or uuid.uuid4().hex,
        "role": role,
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

    requested_kind = raw.get("kind")
    if allow_group:
        # 最上位のボタンはflyout/macro/auto_attr/layer_snapshotいずれも可。
        allowed_kinds = BUTTON_KINDS_GROUP + (BUTTON_KIND_AUTO_ATTR, BUTTON_KIND_LAYER_SNAPSHOT)
    else:
        # 👑 sub_buttons(箱の中身)は入れ子の箱(flyout/macro)は禁止だが、
        # auto_attrは中身自体がsub_buttonsを持たないので入れ子にならず
        # 許可する(ユーザー要望:「グループボタンの中には線属性ボタン
        # 作れますか？」)。
        allowed_kinds = (BUTTON_KIND_AUTO_ATTR,)
    kind = requested_kind if requested_kind in allowed_kinds else BUTTON_KIND_SINGLE

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

    if kind in BUTTON_KINDS_GROUP:
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
    elif kind == BUTTON_KIND_AUTO_ATTR:
        line_color = raw.get("line_color")
        if line_color not in LINE_COLOR_CTRL_IDS:
            line_color = DEFAULT_LINE_COLOR_CTRL_ID
        line_type = raw.get("line_type")
        if line_type not in LINE_TYPE_CTRL_IDS:
            line_type = DEFAULT_LINE_TYPE_CTRL_ID
        button["line_color"] = line_color
        button["line_type"] = line_type
        button["line_width"] = str(raw.get("line_width") or "")
        button["horizontal_vertical"] = bool(raw.get("horizontal_vertical"))
        layer_group = raw.get("layer_group")
        button["layer_group"] = layer_group if isinstance(layer_group, int) and 0 <= layer_group <= 15 else None
        layer_number = raw.get("layer_number")
        button["layer_number"] = layer_number if isinstance(layer_number, int) and 0 <= layer_number <= 15 else None
        target_command = str(raw.get("target_command") or "").strip()
        button["target_command"] = target_command or DEFAULT_AUTO_ATTR_TARGET_COMMAND
    elif kind == BUTTON_KIND_LAYER_SNAPSHOT:
        snapshot_id = str(raw.get("snapshot_id") or "").strip()
        button["snapshot_id"] = snapshot_id or uuid.uuid4().hex
        role = raw.get("role")
        button["role"] = role if role in LAYER_SNAPSHOT_ROLES else LAYER_SNAPSHOT_ROLE_RESTORE

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
