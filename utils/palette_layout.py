# ===== ✂️ utils/palette_layout.py START ✂️ =====
"""
左右パレットをjw_cadのメインウィンドウにドッキングさせるための
純粋なジオメトリ計算。tkinter/win32に依存しないため、実機を
起動しなくても計算結果を検証できる。
"""

OUTER_PAD = 3
PIN_BUTTON_HEIGHT = 23
DEFAULT_BUTTON_SIZE = 48


def _toolbar_size(side):
    """
    side: {"groups": int, "max_group_len": int, "button_count": int,
           "button_size": int, "orientation": "portrait"|"landscape"}

    portrait: groups=列数（左右に並ぶ）、max_group_len=一番長い列の行数。
    landscape: groups=行数（上下に並ぶ）、max_group_len=一番長い行のボタン数。
    """
    groups = int(side.get("groups", 0) or 0)
    extent = int(side.get("max_group_len", 0) or 0)
    count = int(side.get("button_count", 0) or 0)
    size = int(side.get("button_size", DEFAULT_BUTTON_SIZE) or DEFAULT_BUTTON_SIZE)

    if count <= 0 or groups <= 0 or extent <= 0:
        return 0, 0

    if side.get("orientation") == "landscape":
        cells_w, cells_h = extent, groups
    else:
        cells_w, cells_h = groups, extent

    width = (cells_w * size) + (OUTER_PAD * 2)
    height = (cells_h * size) + PIN_BUTTON_HEIGHT + (OUTER_PAD * 2)
    return width, height


EDGE_LEFT = "left"
EDGE_RIGHT = "right"

# 👑 N枚パレット対応(2026-09-09、実装1歩目)。今回のスコープでは「好きな
# 辺に」は見送り、既存の左右ドッキングのままパレット数だけ増やせるように
# する(doc/HANDOFF等ではなく[[jwnavigator-backlog-decisions]]メモリ参照)。
# 新しいパレットのキーは"左"/"右"を流用せず新規キー(例:"palette_3")を
# 足す方針のため、そのキーがどちら側にドッキングするかをここで対応付ける。
# 将来、設定画面に「辺を選ぶ」UIができたら、ここを設定ファイル駆動に
# 差し替える想定(今は決め打ちのフォールバックのみ)。
DEFAULT_EDGES = {"左": EDGE_LEFT, "右": EDGE_RIGHT}


def _edge_for(side_key, edges, index):
    if edges and side_key in edges:
        return edges[side_key]
    if side_key in DEFAULT_EDGES:
        return DEFAULT_EDGES[side_key]
    # 未知のキー(3枚目以降)はいったん左右交互に割り振る。
    return EDGE_LEFT if index % 2 == 0 else EDGE_RIGHT


def compute_palette_geometry(jw_rect, screen_width, virtual_screen, sides, edges=None):
    """
    jw_rect: jw_cadメインウィンドウの (x1, y1, x2, y2)。
    screen_width: 最大化判定に使うプライマリスクリーン幅。
    virtual_screen: 画面外クランプに使う (left, top, width, height)
                     （マルチモニター込みの仮想スクリーン全体）。
    sides: {side_key: side辞書, ...} (_toolbar_size()が受け取る形式)。
           2枚時代の呼び出し互換のため、キーの並び順はdictの挿入順で
           扱う(Python 3.7+のdictは順序を保持する)。
    edges: {side_key: EDGE_LEFT|EDGE_RIGHT, ...}(省略時はDEFAULT_EDGESと
           交互割り振りにフォールバック)。

    戻り値: {side_key: (w, h, x, y) または None, ...}
    ボタンが0個の側はNoneを返す（呼び出し側で「何もしない」判断に使う）。
    """
    x1, y1, x2, y2 = jw_rect
    jw_w = x2 - x1

    sizes = {key: _toolbar_size(cfg) for key, cfg in sides.items()}

    # 最大化時、jw_cadの実ウィンドウ矩形は見えない分のリサイズ境界を
    # 含んで画面幅を超えることがある（Windowsの仕様）ため、通常配置とは
    # 別ロジックでドッキング位置を決める。
    is_maximized = x1 <= 0 and y1 <= 0 and jw_w >= screen_width - 20
    top_off = 70 if is_maximized else 0

    v_left, v_top, v_width, v_height = virtual_screen
    top_y = y1 + top_off

    def _clamp(x, y, w, h):
        cx = max(v_left, min(x, v_left + v_width - w))
        cy = max(v_top, min(y, v_top + v_height - h))
        return (w, h, cx, cy)

    result = {}
    for i, (key, cfg) in enumerate(sides.items()):
        tb_w, tb_h = sizes[key]
        if int(cfg.get("button_count", 0) or 0) <= 0:
            result[key] = None
            continue
        edge = _edge_for(key, edges, i)
        if is_maximized:
            x = 0 if edge == EDGE_LEFT else jw_w - tb_w - 16
        else:
            x = x1 - tb_w if edge == EDGE_LEFT else x2
        result[key] = _clamp(x, top_y, tb_w, tb_h)
    return result
# ===== ✂️ utils/palette_layout.py END ✂️ =====
