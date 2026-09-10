# ===== ✂️ utils/palette_layout.py START ✂️ =====
"""
左右パレットをjw_cadのメインウィンドウにドッキングさせるための
純粋なジオメトリ計算。tkinter/win32に依存しないため、実機を
起動しなくても計算結果を検証できる。
"""

OUTER_PAD = 3
PIN_BUTTON_HEIGHT = 23
DEFAULT_BUTTON_SIZE = 48
# 👑 「左辺の上につける時は上に隙間、上辺の左につける時は左に隙間」
# (ユーザー要望、2026-09-10)。辺同士が角で接する組み合わせ(例:
# 左辺・上端と上辺・左端)がぴったりくっつかないよう常時空ける余白。
# ユーザーが実機で12か所すべてに自由配置のパレットを置いて実測した
# ところ、既存のtop_off(最大化時にjw_cad自身のメニュー分を避ける量)と
# ほぼ同じ70px前後だったため、同じ値を採用する(意味的には別概念だが、
# 「1の追従自動配置と同じくらいの隙間感」という要望にも合う)。
CORNER_GAP = 70


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

    # 👑 「追従/自由ボタンは横型の時、左の先頭へ」(2026-09-10)。縦型は
    # 従来通りpin_btnが上に乗る分だけ高さに足すが、横型はpin_btnが
    # ボタン列と横並び(左端)になるので、高さではなく幅に足す
    # (widgets/toolbar.pyの_layout_chrome()参照)。
    if side.get("orientation") == "landscape":
        cells_w, cells_h = extent, groups
        width = (cells_w * size) + PIN_BUTTON_HEIGHT + (OUTER_PAD * 2)
        height = (cells_h * size) + (OUTER_PAD * 2)
    else:
        cells_w, cells_h = groups, extent
        width = (cells_w * size) + (OUTER_PAD * 2)
        height = (cells_h * size) + PIN_BUTTON_HEIGHT + (OUTER_PAD * 2)
    return width, height


EDGE_LEFT = "left"
EDGE_RIGHT = "right"
EDGE_TOP = "top"
EDGE_BOTTOM = "bottom"
EDGES = (EDGE_LEFT, EDGE_RIGHT, EDGE_TOP, EDGE_BOTTOM)

POS_START = "start"    # 左/右辺なら上寄り、上/下辺なら左寄り
POS_CENTER = "center"
POS_END = "end"         # 左/右辺なら下寄り、上/下辺なら右寄り
POSITIONS = (POS_START, POS_CENTER, POS_END)

# 👑 N枚パレット対応(2026-09-09、実装1歩目)。当初は「好きな辺に」は
# 見送っていたが、2026-09-10にユーザーから「上下も含めた4方向、かつ
# 各辺の端と真ん中の12か所」に対応してほしいと要望があり、この関数を
# 4辺×3位置(start/center/end)のマトリクスへ拡張した([[jwnavigator-
# backlog-decisions]]メモリ参照)。
# 新しいパレットのキーは"左"/"右"を流用せず新規キー(例:"palette_3")を
# 足す方針のため、そのキーがどこにドッキングするかをここで対応付ける。
DEFAULT_EDGES = {"左": EDGE_LEFT, "右": EDGE_RIGHT}


def _edge_for(side_key, edges, index):
    if edges and side_key in edges and edges[side_key] in EDGES:
        return edges[side_key]
    if side_key in DEFAULT_EDGES:
        return DEFAULT_EDGES[side_key]
    # 未知のキー(3枚目以降)で明示指定が無い場合はいったん左右交互に割り振る。
    return EDGE_LEFT if index % 2 == 0 else EDGE_RIGHT


def _position_for(side_key, positions, index):
    if positions and side_key in positions and positions[side_key] in POSITIONS:
        return positions[side_key]
    return POS_START


def compute_palette_geometry(jw_rect, screen_width, virtual_screen, sides, edges=None, positions=None, prevent_overlap=True):
    """
    jw_rect: jw_cadメインウィンドウの (x1, y1, x2, y2)。
    screen_width: 最大化判定に使うプライマリスクリーン幅。
    virtual_screen: 画面外クランプに使う (left, top, width, height)
                     （マルチモニター込みの仮想スクリーン全体）。
    sides: {side_key: side辞書, ...} (_toolbar_size()が受け取る形式)。
           2枚時代の呼び出し互換のため、キーの並び順はdictの挿入順で
           扱う(Python 3.7+のdictは順序を保持する)。
    edges: {side_key: EDGE_LEFT|EDGE_RIGHT|EDGE_TOP|EDGE_BOTTOM, ...}
           (省略/未指定時はDEFAULT_EDGESと交互割り振りにフォールバック)。
    positions: {side_key: POS_START|POS_CENTER|POS_END, ...}(省略/未指定時
           はPOS_START=辺の開始寄り、従来と同じ見た目)。左/右辺では
           start=上寄り・center=縦中央・end=下寄り、上/下辺ではstart=左寄り・
           center=横中央・end=右寄りを意味する(4辺×3位置=12か所)。
    prevent_overlap: True(既定)なら、同じ(辺,位置)の組を割り当てられた
           パレットが複数ある場合、その組ごとにdictの挿入順でスタッキング
           軸方向(左右辺ならy、上下辺ならx)へ積み上げて重なりを避ける。
           Falseなら従来通り全員同じ基準位置に配置する(意図的に重ねて
           片方だけ自由配置で退避させる運用向け)。

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
        # 👑 wm_geometry()は整数px以外(例:"221x54+567.0+0")を
        # "bad geometry specifier"として拒否する(実測で発覚、2026-09-10:
        # center位置の/2計算がfloatを生み、追従復帰時に位置更新が
        # 毎tick例外で失敗し続けて「追従にしても動かない」ように見えた)。
        # ここで最終的に必ずintへ丸める。
        cx = int(round(max(v_left, min(x, v_left + v_width - w))))
        cy = int(round(max(v_top, min(y, v_top + v_height - h))))
        return (w, h, cx, cy)

    def _base_for(edge, pos, tb_w, tb_h):
        # 戻り値: (base_x, base_y, stacking_axis) 。stacking_axisは
        # prevent_overlapで積み上げる向き("y"=左右辺、"x"=上下辺)。
        # 👑 実機で12か所すべてに自由配置のパレットを置いて実測した結果
        # (2026-09-10)、以下のパターンが判明:
        # ・左右辺の開始位置(上寄り)は、既存のtop_offだけで十分な隙間が
        #   でき、追加のCORNER_GAPは不要(むしろ足すとズレた)。
        # ・左右辺の終了位置(下寄り)には、下辺ドッキングとぶつからない
        #   ようCORNER_GAPが要る。
        # ・上辺ドッキングは画面最上部にほぼ隙間なくフラッシュ。左右辺の
        #   開始位置と角でぶつからないよう、横方向(x)にCORNER_GAPが要る。
        # ・下辺ドッキングは、タスクバー等を避けてか画面最下部から
        #   CORNER_GAP分浮いていた。横方向のCORNER_GAPは上辺と同様。
        if edge in (EDGE_LEFT, EDGE_RIGHT):
            if is_maximized:
                fixed_x = 0 if edge == EDGE_LEFT else jw_w - tb_w - 16
            else:
                fixed_x = x1 - tb_w if edge == EDGE_LEFT else x2
            dock_top, dock_bottom = top_y, y2
            span = dock_bottom - dock_top
            if pos == POS_CENTER:
                base_y = dock_top + max(0, span - tb_h) // 2
            elif pos == POS_END:
                base_y = dock_bottom - tb_h - CORNER_GAP
            else:
                base_y = dock_top
            return fixed_x, base_y, "y"
        else:
            # 👑 上辺ドッキングは、非最大化時は「ウィンドウの外側(上)」に
            # 出す("y1 - tb_h")が、最大化時はその外側が画面外になるため、
            # 画面最上部にフラッシュ(隙間なし)で配置する("y1"、_clamp()で
            # 0付近に丸められる)。下辺は逆に、最大化時に画面最下部との
            # 間へCORNER_GAP分の隙間を空ける(タスクバー等を避ける想定、
            # 実測でこの量だった)。
            if edge == EDGE_TOP:
                fixed_y = y1 if is_maximized else y1 - tb_h
            else:
                fixed_y = y2 - CORNER_GAP if is_maximized else y2
            dock_left, dock_right = x1, x2
            span = dock_right - dock_left
            if pos == POS_CENTER:
                base_x = dock_left + max(0, span - tb_w) // 2
            elif pos == POS_END:
                base_x = dock_right - tb_w - CORNER_GAP
            else:
                base_x = dock_left + CORNER_GAP
            return base_x, fixed_y, "x"

    # 👑 「同じ配置を指定されたときにはずらす。どんどん縦に積まないで」
    # (ユーザー要望、2026-09-10)。固定の小さいpx値でずらすと、パレット
    # 自身の幅より小さければ結局重なってしまう(実測で発覚)。確実に
    # 重ならないよう、直前までに同じスロットへ置かれたパレットの「内側」
    # 方向のサイズ(左辺/右辺なら幅、上辺/下辺なら高さ)の合計ぶんだけ
    # ずらす。積み上げ軸方向(左辺/右辺ならy、上辺/下辺ならx)には一切
    # 伸びない。
    INWARD_DX = {EDGE_LEFT: 1, EDGE_RIGHT: -1, EDGE_TOP: 0, EDGE_BOTTOM: 0}
    INWARD_DY = {EDGE_LEFT: 0, EDGE_RIGHT: 0, EDGE_TOP: 1, EDGE_BOTTOM: -1}

    result = {}
    stack = {}  # (edge, pos) -> 内側方向へ積み上がった累計サイズ(px)
    for i, (key, cfg) in enumerate(sides.items()):
        tb_w, tb_h = sizes[key]
        if int(cfg.get("button_count", 0) or 0) <= 0:
            result[key] = None
            continue
        edge = _edge_for(key, edges, i)
        pos = _position_for(key, positions, i)
        base_x, base_y, axis = _base_for(edge, pos, tb_w, tb_h)
        slot_key = (edge, pos)
        # 👑 「自由(ピン留め)配置のパレットは、追従中の他パレットのずらし
        # 計算から除外してほしい」(ユーザー要望、2026-09-10)。自由中は
        # 実際の座標がここでは反映されない(main.py側でwinfo_x/yに
        # 差し替えられる)ため、ここで律儀にスロットを予約すると、
        # ドラッグでどこかへ避けたはずの自由パレットの「本来の場所」を
        # 追従中の他パレットがいつまでも避け続けてしまう。追従同士
        # (is_pinnedでない者同士)だけがスロットを取り合う。
        is_pinned = bool(cfg.get("is_pinned", False))
        inward_size = tb_w if axis == "y" else tb_h

        offset = 0
        if prevent_overlap and not is_pinned:
            offset = stack.get(slot_key, 0)
            stack[slot_key] = offset + inward_size

        dx = offset * INWARD_DX[edge]
        dy = offset * INWARD_DY[edge]
        x, y = base_x + dx, base_y + dy
        result[key] = _clamp(x, y, tb_w, tb_h)
    return result
# ===== ✂️ utils/palette_layout.py END ✂️ =====
