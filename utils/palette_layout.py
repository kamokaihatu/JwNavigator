# ===== ✂️ utils/palette_layout.py START ✂️ =====
"""
左右パレットをjw_cadのメインウィンドウにドッキングさせるための
純粋なジオメトリ計算。tkinter/win32に依存しないため、実機を
起動しなくても計算結果を検証できる。
"""

OUTER_PAD = 3
BUTTON_SIZE = 48
PIN_BUTTON_HEIGHT = 23


def _toolbar_size(cols, max_rows, button_count):
    if button_count <= 0 or cols <= 0:
        return 0, 0
    width = (cols * BUTTON_SIZE) + (OUTER_PAD * 2)
    height = (max_rows * BUTTON_SIZE) + PIN_BUTTON_HEIGHT + (OUTER_PAD * 2)
    return width, height


def compute_palette_geometry(jw_rect, screen_width, virtual_screen, left, right):
    """
    jw_rect: jw_cadメインウィンドウの (x1, y1, x2, y2)。
    screen_width: 最大化判定に使うプライマリスクリーン幅。
    virtual_screen: 画面外クランプに使う (left, top, width, height)
                     （マルチモニター込みの仮想スクリーン全体）。
    left / right: {"cols": int, "max_rows": int, "button_count": int}

    戻り値: {"左": (w, h, x, y) または None, "右": (同上)}
    ボタンが0個の側はNoneを返す（呼び出し側で「何もしない」判断に使う）。
    """
    x1, y1, x2, y2 = jw_rect
    jw_w = x2 - x1

    tb_w_l, tb_h_l = _toolbar_size(left["cols"], left["max_rows"], left["button_count"])
    tb_w_r, tb_h_r = _toolbar_size(right["cols"], right["max_rows"], right["button_count"])

    # 最大化時、jw_cadの実ウィンドウ矩形は見えない分のリサイズ境界を
    # 含んで画面幅を超えることがある（Windowsの仕様）ため、通常配置とは
    # 別ロジックでドッキング位置を決める。
    is_maximized = x1 <= 0 and y1 <= 0 and jw_w >= screen_width - 20
    if is_maximized:
        left_x = 0
        right_x = jw_w - tb_w_r - 16
        top_off = 70
    else:
        left_x = x1 - tb_w_l
        right_x = x2
        top_off = 0

    v_left, v_top, v_width, v_height = virtual_screen
    top_y = y1 + top_off

    def _clamp(x, y, w, h):
        cx = max(v_left, min(x, v_left + v_width - w))
        cy = max(v_top, min(y, v_top + v_height - h))
        return (w, h, cx, cy)

    result = {"左": None, "右": None}
    if left["button_count"] > 0:
        result["左"] = _clamp(left_x, top_y, tb_w_l, tb_h_l)
    if right["button_count"] > 0:
        result["右"] = _clamp(right_x, top_y, tb_w_r, tb_h_r)
    return result
# ===== ✂️ utils/palette_layout.py END ✂️ =====
